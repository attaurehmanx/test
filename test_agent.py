#!/usr/bin/env python3
"""
Script to test the agent service directly
"""

import os
from services.agent_service import agent_service

def test_agent():
    """Test the agent service directly"""
    print(f"Agent service provider: {agent_service.provider}")
    print(f"Agent service model: {agent_service.model}")

    # Test query
    test_query = "What is robotics?"
    test_context = [{
        "content": "Robotics is an interdisciplinary branch of engineering and science that includes mechanical engineering, electrical engineering, computer science, and others. Robotics deals with the design, construction, operation, and use of robots, as well as computer systems for their control, sensory feedback, and information processing.",
        "title": "Introduction to Robotics",
        "url": "/docs/intro-robotics",
        "relevance_score": 0.64
    }]

    print(f"\nTesting agent with query: '{test_query}'")
    print(f"Context: {test_context[0]['content'][:100]}...")

    try:
        result = agent_service.generate_response(
            query=test_query,
            context=test_context
        )
        print(f"\nResult: {result}")
    except Exception as e:
        print(f"\nError generating response: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_agent()