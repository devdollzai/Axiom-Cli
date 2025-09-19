import argparse

def main():
    parser = argparse.ArgumentParser(description='Sovereign Gemini CLI')
    parser.add_argument('--nl', help='Natural language command')
    parser.add_argument('--context-id', default='default')
    args = parser.parse_args()

    # Placeholder for orchestrator call
    if args.nl:
        print(f"Processing NL: {args.nl} with context {args.context_id}")
    else:
        print("Use --nl for natural language commands")

if __name__ == '__main__':
    main()