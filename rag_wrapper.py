import sys, json, argparse

sys.path.insert(0, r'C:\Users\lenovo\.agents\skills-router\security-skill-router\skills-rag')

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('query')
    parser.add_argument('--mode', choices=['soc_rag', 'skills_rag'], default='skills_rag')
    parser.add_argument('--platform', default='unknown')
    parser.add_argument('--skill', default='')
    parser.add_argument('--top-k', type=int, default=None)
    args = parser.parse_args()
    
    if args.mode == 'soc_rag':
        import soc_rag
        result = soc_rag.search(args.query, top_k=args.top_k or 6)
    else:
        import skills_rag
        decision = {'platform': args.platform}
        if args.skill:
            decision['skill'] = args.skill
        result = skills_rag.search(args.query, top_k=args.top_k, decision=decision)
    print(json.dumps(result, ensure_ascii=False))

if __name__ == '__main__':
    main()
