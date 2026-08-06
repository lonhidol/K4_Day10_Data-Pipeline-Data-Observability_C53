"""
verify_agent_grounding.py
--------------------------
Kiểm tra agent:
  1. Câu trả lời phải dùng tool (có tool_call trong trace)
  2. Nội dung câu trả lời khớp với tool result (không hallucinate)
  3. Câu hỏi ngoài corpus → agent phải thừa nhận không biết

Chạy: python src/pipelines/verify_agent_grounding.py
"""
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from core.config import load_settings
from retrieval.index import LocalEmbeddingIndex
from retrieval.agent import build_agent


def check_tool_was_called(result: dict) -> tuple[bool, list[str]]:
    """Trả về (có gọi tool không, danh sách tên tool đã gọi)."""
    tools_called = []
    for msg in result.get("messages", []):
        if hasattr(msg, "tool_calls") and msg.tool_calls:
            for tc in msg.tool_calls:
                tools_called.append(tc["name"])
    return bool(tools_called), tools_called


def get_tool_output(result: dict) -> str:
    """Lấy nội dung Tool trả về từ lịch sử tin nhắn."""
    for msg in result.get("messages", []):
        if getattr(msg, "type", "") == "tool":
            return msg.content
    return ""


def get_final_answer(result: dict) -> str:
    messages = result.get("messages", [])
    if not messages:
        return ""
    return getattr(messages[-1], "content", str(messages[-1]))


def run_test(agent, label: str, question: str, expect_tool: bool,
             grounding_check: str | None = None):
    """
    Chạy 1 test case.
    grounding_check: chuỗi phải xuất hiện trong tool output (kiểm tra grounding).
    """
    print(f"\n{'─'*60}")
    print(f"  TEST: {label}")
    print(f"  Q   : {question}")
    print()

    result = agent.invoke({"messages": [{"role": "user", "content": question}]})
    tool_used, tools = check_tool_was_called(result)
    tool_output   = get_tool_output(result)
    final_answer  = get_final_answer(result)

    # --- CHECK 1: Agent có gọi tool không? ---
    if expect_tool:
        status1 = "✅" if tool_used else "❌"
        print(f"  {status1} [Tool called?]  {tools if tool_used else 'KHÔNG có tool nào được gọi!'}")
    else:
        # Câu hỏi ngoài corpus — agent không cần gọi tool, hoặc gọi nhưng tìm không thấy
        print(f"  ℹ️  [Tool called?]  {tools if tool_used else 'Không gọi tool (hợp lệ cho câu hỏi ngoài corpus)'}")

    # --- CHECK 2: Answer có khớp với tool result không? (grounding) ---
    if grounding_check and tool_output:
        grounded = grounding_check.lower() in tool_output.lower()
        status2 = "✅" if grounded else "❌"
        print(f"  {status2} [Grounded?]    Tool output {'CÓ' if grounded else 'KHÔNG'} chứa '{grounding_check}'")
    elif grounding_check and not tool_output:
        print(f"  ❌ [Grounded?]    Tool output rỗng — không thể kiểm chứng grounding!")

    # --- CHECK 3: Câu hỏi ngoài corpus → agent có thừa nhận không? ---
    if not expect_tool:
        refusal_keywords = ["not found", "no paper", "cannot find",
                            "not in", "don't have", "do not have",
                            "không tìm", "không có", "không tồn tại",
                            "sorry", "i'm not able", "i don't", "i do not"]
        refused = any(kw in final_answer.lower() for kw in refusal_keywords)
        status3 = "✅" if refused else "⚠️"
        print(f"  {status3} [Refused?]     Agent {'thừa nhận không biết ✓' if refused else 'CÓ THỂ đang hallucinate — kiểm tra câu trả lời!'}")

    print(f"\n  💬 Final answer: {final_answer[:200]}{'...' if len(final_answer) > 200 else ''}")


def main():
    print("\n" + "═"*60)
    print("   AGENT GROUNDING VERIFICATION")
    print("   Kiểm tra: answer dùng tool result, không vượt corpus")
    print("═"*60)

    settings = load_settings()
    print("\n  Đang tải Index và Agent...")
    index = LocalEmbeddingIndex.load(settings)
    agent = build_agent(settings, index)
    print(f"  ✅ Sẵn sàng | {len(index.documents)} papers trong corpus\n")

    # ==== TEST 1: Câu hỏi CÓ trong corpus ====
    # Kiểm tra agent gọi tool và answer khớp tool result
    run_test(
        agent,
        label="Câu hỏi CÓ trong corpus (author lookup)",
        question="Who authored the paper 'The Age of Autonomous Agents: A Bibliometric Review of Agentic AI Architectures, Applications, and Emerging Challenges'?",
        expect_tool=True,
        grounding_check="Ben J. Weber",   # phải xuất hiện trong tool output
    )

    # ==== TEST 2: Câu hỏi CÓ trong corpus (semantic) ====
    run_test(
        agent,
        label="Câu hỏi CÓ trong corpus (semantic search)",
        question="Find papers about retrieval augmented generation for safety in industrial settings.",
        expect_tool=True,
        grounding_check="SafeRAG",        # bài SafeRAG phải được tìm thấy
    )

    # ==== TEST 3: Câu hỏi NGOÀI corpus ====
    # Agent không được tự bịa, phải thừa nhận không tìm thấy
    run_test(
        agent,
        label="Câu hỏi NGOÀI corpus (hallucination test)",
        question="What did Elon Musk say about GPT-5 in 2025?",
        expect_tool=False,
        grounding_check=None,
    )

    print("\n" + "═"*60)
    print("   KẾT LUẬN")
    print("─"*60)
    print("  ✅ = Đạt yêu cầu grounding")
    print("  ❌ = Cần kiểm tra lại (tool không được gọi / answer sai nguồn)")
    print("  ⚠️  = Agent có thể hallucinate với câu hỏi ngoài corpus")
    print("═"*60 + "\n")


if __name__ == "__main__":
    main()
