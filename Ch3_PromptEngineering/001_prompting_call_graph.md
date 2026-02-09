# 001_prompting.ipynb クラス・関数呼び出し関係

## 1. クラス図（PromptEvaluator）

```mermaid
classDiagram
    class PromptEvaluator {
        -int max_concurrent_tasks
        __init__(max_concurrent_tasks)
        render(template_string, variables) str
        generate_unique_ideas(task_description, prompt_inputs_spec, num_cases) list
        generate_test_case(task_description, idea, prompt_inputs_spec) dict
        generate_dataset(task_description, prompt_inputs_spec, num_cases, output_file) list
        grade_output(test_case, output, extra_criteria) dict
        run_test_case(test_case, run_prompt_function, extra_criteria) dict
        run_evaluation(run_prompt_function, dataset_file, extra_criteria, json_output_file, html_output_file) list
    }
```

## 2. 関数・モジュール一覧（クラス外）

| 名前 | 役割 |
|------|------|
| `add_user_message(messages, text)` | messages に user メッセージを追加 |
| `add_assistant_message(messages, text)` | messages に assistant メッセージを追加 |
| `chat(messages, system, temperature, stop_sequences)` | Anthropic API で会話しテキストを返す |
| `generate_prompt_evaluation_report(evaluation_results)` | 評価結果から HTML レポート文字列を生成 |

## 3. 呼び出し関係フロー図

```mermaid
flowchart TB
    subgraph notebook["ノートブック実行フロー"]
        C4["Cell 4: evaluator = PromptEvaluator()"]
        C5["Cell 5: evaluator.generate_dataset()"]
        C6["Cell 6: run_prompt() 定義"]
        C7["Cell 7: evaluator.run_evaluation(run_prompt)"]
        C4 --> C5 --> C6 --> C7
    end

    subgraph helpers["ヘルパー関数"]
        add_user["add_user_message()"]
        add_asst["add_assistant_message()"]
        chat_fn["chat()"]
    end

    subgraph evaluator["PromptEvaluator"]
        render["render()"]
        gen_ideas["generate_unique_ideas()"]
        gen_case["generate_test_case()"]
        gen_dataset["generate_dataset()"]
        grade["grade_output()"]
        run_tc["run_test_case()"]
        run_eval["run_evaluation()"]
    end

    subgraph report["レポート"]
        gen_report["generate_prompt_evaluation_report()"]
    end

    gen_dataset --> gen_ideas
    gen_dataset --> gen_case
    run_eval --> run_tc
    run_eval --> gen_report

    gen_ideas --> render
    gen_ideas --> add_user
    gen_ideas --> add_asst
    gen_ideas --> chat_fn

    gen_case --> render
    gen_case --> add_user
    gen_case --> add_asst
    gen_case --> chat_fn

    run_tc --> grade
    run_tc --> run_prompt["run_prompt() コールバック"]

    grade --> render
    grade --> add_user
    grade --> add_asst
    grade --> chat_fn

    run_prompt --> add_user
    run_prompt --> chat_fn
```

## 4. メソッド別の内部呼び出し詳細

```mermaid
flowchart LR
    subgraph PE["PromptEvaluator"]
        render
        gen_ideas
        gen_case
        gen_dataset
        grade
        run_tc
        run_eval
    end

    gen_dataset -->|"1. アイデア生成"| gen_ideas
    gen_dataset -->|"2. 各アイデアでテストケース生成"| gen_case

    gen_ideas --> render
    gen_case --> render
    grade --> render

    gen_ideas --> add_user
    gen_ideas --> add_asst
    gen_ideas --> chat
    gen_case --> add_user
    gen_case --> add_asst
    gen_case --> chat
    grade --> add_user
    grade --> add_asst
    grade --> chat

    run_eval -->|"各テストケースで"| run_tc
    run_tc -->|"1. プロンプト実行"| run_prompt
    run_tc -->|"2. 採点"| grade
    run_eval -->|"レポート生成"| gen_report
```

## 5. シーケンス図（評価実行時）

```mermaid
sequenceDiagram
    participant User
    participant run_evaluation
    participant run_test_case
    participant run_prompt
    participant grade_output
    participant chat
    participant gen_report

    User->>run_evaluation: run_evaluation(run_prompt, dataset_file)
    run_evaluation->>run_evaluation: json.load(dataset_file)
    loop 各 test_case
        run_evaluation->>run_test_case: run_test_case(test_case, run_prompt, ...)
        run_test_case->>run_prompt: run_prompt(prompt_inputs)
        run_prompt->>chat: chat(messages)
        chat-->>run_prompt: output
        run_prompt-->>run_test_case: output
        run_test_case->>grade_output: grade_output(test_case, output, ...)
        grade_output->>chat: chat(eval_prompt)
        chat-->>grade_output: eval_json
        grade_output-->>run_test_case: { score, reasoning, ... }
        run_test_case-->>run_evaluation: result
    end
    run_evaluation->>gen_report: generate_prompt_evaluation_report(results)
    gen_report-->>run_evaluation: html
    run_evaluation-->>User: results
```

## 6. 依存関係サマリ

| 呼び出し元 | 呼び出し先 |
|------------|------------|
| `generate_dataset` | `generate_unique_ideas`, `generate_test_case` |
| `run_evaluation` | `run_test_case`, `generate_prompt_evaluation_report`, `mean` |
| `run_test_case` | `run_prompt`（引数）, `grade_output` |
| `generate_unique_ideas` | `render`, `add_user_message`, `add_assistant_message`, `chat` |
| `generate_test_case` | `render`, `add_user_message`, `add_assistant_message`, `chat` |
| `grade_output` | `render`, `add_user_message`, `add_assistant_message`, `chat` |
| `run_prompt`（ユーザー定義） | `add_user_message`, `chat` |

外部ライブラリ: `anthropic.Anthropic`, `json`, `re`, `textwrap.dedent`, `statistics.mean`, `concurrent.futures`, `dotenv.load_dotenv`
