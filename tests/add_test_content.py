#!/usr/bin/env python3
"""
Script to add test content to the Qdrant database
"""

import uuid
from services.rag_service import rag_service

def add_test_documents():
    """Add some test documents to the Qdrant database"""

    # Test documents about robotics and AI
    test_documents = [
        {
            "title": "Introduction to Robotics",
            "content": "Robotics is an interdisciplinary branch of engineering and science that includes mechanical engineering, electrical engineering, computer science, and others. Robotics deals with the design, construction, operation, and use of robots, as well as computer systems for their control, sensory feedback, and information processing.",
            "url": "/docs/intro-robotics"
        },
        {
            "title": "Artificial Intelligence in Robotics",
            "content": "Artificial intelligence in robotics involves the combination of AI algorithms with robotic systems to create intelligent machines. These systems can perceive their environment, make decisions, and perform tasks autonomously or semi-autonomously. Machine learning, computer vision, and natural language processing are key components of AI in robotics.",
            "url": "/docs/ai-robotics"
        },
        {
            "title": "ROS 2 Framework",
            "content": "ROS 2 (Robot Operating System 2) is a flexible framework for writing robot software. It is a collection of tools, libraries, and conventions that aim to simplify the task of creating complex and robust robot behavior across a wide variety of robot platforms. ROS 2 provides hardware abstraction, device drivers, libraries, visualizers, message-passing, package management, and more.",
            "url": "/docs/ros2-framework"
        },
        {
            "title": "Humanoid Robots",
            "content": "Humanoid robots are robots that have a human-like body structure with a head, torso, two arms, and two legs. They are designed to imitate human behavior and movements. Humanoid robots are used in research, entertainment, and increasingly in practical applications such as customer service and healthcare assistance.",
            "url": "/docs/humanoid-robots"
        },
        {
            "title": "Gazebo Simulation",
            "content": "Gazebo is a robot simulation environment that provides realistic 3D simulation of robots and their environments. It offers high-fidelity physics simulation, detailed 3D rendering, and support for various sensors. Gazebo is commonly used in robotics development to test algorithms and robot designs before deployment on physical robots.",
            "url": "/docs/gazebo-simulation"
        }
    ]

    print("Adding test documents to Qdrant database...")

    success_count = 0
    for i, doc in enumerate(test_documents, 1):
        print(f"Adding document {i}: {doc['title']}")

        success = rag_service.add_document_to_index(
            content=doc['content'],
            title=doc['title'],
            url=doc['url']
        )

        if success:
            success_count += 1
            print(f"  [SUCCESS] Successfully added")
        else:
            print(f"  [FAILED] Failed to add")

    print(f"\nSuccessfully added {success_count} out of {len(test_documents)} documents.")

    if success_count > 0:
        print("\nYou can now test the system with queries like:")
        print("  - 'What is robotics?'")
        print("  - 'Tell me about ROS 2'")
        print("  - 'What are humanoid robots?'")
        print("  - 'How does Gazebo work?'")
        print("\nUse: python retrieve.py --query 'your question here'")

if __name__ == "__main__":
    add_test_documents()