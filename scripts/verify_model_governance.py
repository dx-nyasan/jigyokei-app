
import os
import sys
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("verify-governance")

# Add project root to sys.path
sys.path.append(os.path.abspath(os.curdir))

from src.core.model_commander import get_commander
from src.core.jigyokei_core import AIInterviewer
from src.core.manual_rag import get_rag

def test_generate_content():
    logger.info("Testing generate_content via ModelCommander...")
    commander = get_commander()
    response = commander.generate_content("reasoning", "Hello, summarize the purpose of Jigyokei in one sentence.")
    logger.info(f"Response: {response.text}")
    assert len(response.text) > 0

def test_embed_content():
    logger.info("Testing embed_content via ModelCommander...")
    commander = get_commander()
    embedding = commander.embed_content("災害対策の重要性について")
    logger.info(f"Embedding dimensions: {len(embedding)}")
    assert len(embedding) > 0

def test_ai_interviewer_integration():
    logger.info("Testing AIInterviewer refactored integration...")
    interviewer = AIInterviewer()
    response = interviewer.send_message("こんにちは、事業内容について相談したいです。")
    logger.info(f"AI Response: {response[:100]}...")
    assert len(response) > 0

def test_manual_rag_integration():
    logger.info("Testing ManualRAG refactored integration...")
    rag = get_rag()
    results = rag.vector_search("地震の想定", top_k=1)
    if results:
        logger.info(f"Top Search Result: {results[0].text[:100]}...")
    else:
        logger.info("No results found (maybe DB is empty), but check if it didn't crash.")

if __name__ == "__main__":
    try:
        test_generate_content()
        test_embed_content()
        test_ai_interviewer_integration()
        test_manual_rag_integration()
        logger.info("✅ All verifications passed!")
    except Exception as e:
        logger.error(f"❌ Verification failed: {e}")
        sys.exit(1)
