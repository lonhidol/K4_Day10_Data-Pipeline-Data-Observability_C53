import sys
from pathlib import Path

# Thêm thư mục src vào sys.path để chạy script độc lập
sys.path.append(str(Path(__file__).resolve().parents[1]))

from core.config import load_settings
from retrieval.index import LocalEmbeddingIndex
from retrieval.agent import build_agent

def main():
    print("--- 🚀 Khởi chạy Agent Test ---")
    settings = load_settings()
    
    print("[1] Đang tải Index...")
    index = LocalEmbeddingIndex.load(settings)
    
    print("[2] Đang khởi tạo Agent (với LLM & Tools)...")
    agent = build_agent(settings, index)
    
    question = "Who authored the paper 'The Age of Autonomous Agents: A Bibliometric Review of Agentic AI Architectures, Applications, and Emerging Challenges'?"
    print(f"\n[3] Gửi câu hỏi cho Agent:\n'{question}'\n")
    
    # Kích hoạt agent và lấy lịch sử tin nhắn
    print("Đang xử lý (đợi AI suy luận và gọi Tool)...\n")
    result = agent.invoke({"messages": [{"role": "user", "content": question}]})
    
    print("="*60)
    print("🔍 KIỂM TRA LỊCH SỬ SUY LUẬN VÀ SỬ DỤNG TOOL CỦA AGENT")
    print("="*60)
    
    for msg in result.get("messages", []):
        role = getattr(msg, "type", type(msg).__name__)
        
        # In ra các quyết định gọi Tool của AI (nếu có)
        if hasattr(msg, "tool_calls") and msg.tool_calls:
            print(f"\n🤖 [AI QUYẾT ĐỊNH GỌI TOOL]:")
            for tool_call in msg.tool_calls:
                print(f"   🔧 Tên Tool : {tool_call['name']}")
                print(f"   📥 Tham số  : {tool_call['args']}")
        
        # In ra kết quả do Tool trả về để kiểm chứng đầu ra
        if role == "tool":
            print(f"\n🛠️ [KẾT QUẢ TỪ TOOL '{msg.name}']: \n{msg.content[:400]}... (đã cắt bớt)\n")
            
    print("="*60)
    print("🎯 CÂU TRẢ LỜI CUỐI CÙNG CỦA AGENT:")
    print("="*60)
    final_message = result.get("messages", [])[-1]
    print(getattr(final_message, "content", str(final_message)))

if __name__ == "__main__":
    main()
