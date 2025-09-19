use pyo3::prelude::*;
use pyo3::types::PyDict;
use serde::{Deserialize, Serialize};
use std::collections::HashMap;

#[derive(Serialize, Deserialize)]
pub struct AgentResult {
    pub output: String,
    pub status: bool,
}

pub struct CognitiveOrchestrator {
    pub active_goals: Vec<String>,
}

impl CognitiveOrchestrator {
    pub fn proactive_plan(&mut self, command: String, context_id: &str) -> Vec<String> {
        let mut subtasks = Python::with_gil(|py| {
            let planner_module = py.import("python.agents.planner_agent")?;
            let planner_class = planner_module.getattr("PlannerAgent")?;
            let planner_inst = planner_class.call0()?;
            let subtasks_py = planner_inst.call_method1("decompose", (command.clone(),))?;
            Ok(subtasks_py.extract::<Vec<String>>()?)
        }).unwrap_or(vec![command]);
        if command.starts_with("--nl") {
            subtasks.insert(0, "check_install_deps".to_string());
        }
        subtasks
    }

    pub fn self_debug(&mut self, result: &AgentResult, orig_cmd: &str, context_id: &str) -> bool {
        if !result.status {
            Python::with_gil(|py| {
                let mem_module = py.import("python.memory")?;
                let mem_inst = mem_module.getattr("QdrantMemory")?.call0()?;
                let payload = PyDict::new(py);
                payload.set_item("type", "error")?;
                mem_inst.call_method1("store_context", (format!("Anomaly: {}", result.output), context_id, payload))?;
                Ok(())
            }).unwrap_or(());
            if result.output.contains("ImportError") {
                let alt = "install missing deps and retry";
                Python::with_gil(|py| {
                    let debug_module = py.import("python.agents.debug_agent")?;
                    let debug_inst = debug_module.getattr("DebugAgent")?.call0()?;
                    let new_plan = debug_inst.call_method1("re_plan", (alt, context_id))?;
                    eprintln!("Re-plan: {}", new_plan.extract::<String>()?);
                    Ok(true)
                }).unwrap_or(false)
            } else if result.output.contains("parse fail") {
                let alt = "replan NL parse";
                Python::with_gil(|py| {
                    let debug_module = py.import("python.agents.debug_agent")?;
                    let debug_inst = debug_module.getattr("DebugAgent")?.call0()?;
                    let new_plan = debug_inst.call_method1("re_plan", (alt, context_id))?;
                    eprintln!("Re-plan: {}", new_plan.extract::<String>()?);
                    Ok(true)
                }).unwrap_or(false)
            } else {
                false
            }
        } else {
            false
        }
    }

    pub fn process(&mut self, command: String, context_id: &str) -> String {
        let mut subtasks = self.proactive_plan(command.clone(), context_id);
        if command.starts_with("--nl") {
            let nl_cmd = command.replace("--nl ", "");
            subtasks = vec!["parse_nl".to_string(), "git_init".to_string(), "add_initial_files".to_string(), "commit".to_string(), "github_push".to_string()];
        }
        self.active_goals.push(command);
        let mut outputs = vec![];
        for sub in subtasks {
            let res = self.dispatch(sub.clone(), context_id);
            outputs.push(res.output.clone());
            if self.self_debug(&res, &sub, context_id) {
                break;
            }
        }
        serde_json::to_string(&outputs).unwrap()
    }

    pub fn dispatch(&mut self, sub_task: String, context_id: &str) -> AgentResult {
        if sub_task == "check_install_deps" {
            Python::with_gil(|py| {
                let os_module = py.import("os")?;
                os_module.call_method1("system", ("pip install -r requirements.txt",))?;
                Ok(AgentResult { output: "Deps installed".to_string(), status: true })
            }).unwrap_or(AgentResult { output: "Dep Install Err".to_string(), status: false })
        } else if sub_task.starts_with("query llm") {
            Python::with_gil(|py| {
                let llm_module = py.import("python.agents.llm_agent")?;
                let llm_inst = llm_module.getattr("LLMAgent")?.call0()?;
                let prompt = sub_task.replace("query llm ", "");
                let output = llm_inst.call_method1("generate", (prompt,))?;
                Ok(AgentResult { output: output.extract::<String>()?, status: true })
            }).unwrap_or(AgentResult { output: "LLM Err".to_string(), status: false })
        } else if sub_task.contains("git") {
            Python::with_gil(|py| {
                let git_module = py.import("python.agents.git_agent")?;
                let git_inst = git_module.getattr("GitAgent")?.call0()?;
                let result_py = git_inst.call_method1("execute_git_action", (sub_task,))?;
                let result_dict: HashMap<String, serde_json::Value> = result_py.extract()?;
                let status = result_dict.get("success").unwrap().as_bool().unwrap_or(false);
                Ok(AgentResult { output: format!("Git: {}", result_dict.get("message").unwrap()), status })
            }).unwrap_or(AgentResult { output: "Git Err".to_string(), status: false })
        } else {
            AgentResult { output: "Unknown task".to_string(), status: false }
        }
    }
}