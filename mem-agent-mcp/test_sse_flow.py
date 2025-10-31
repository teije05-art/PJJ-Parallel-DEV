#!/usr/bin/env python3
"""
Test script for SSE-based multi-iteration planning with Llama improvement analysis.

Simulates the complete flow:
1. Generate planning proposal (GET /api/generate-proposal)
2. User approves proposal
3. Listen to SSE events from /api/execute-plan
4. Auto-approve checkpoints to verify the flow
"""

import asyncio
import json
import httpx
import sys
from typing import Optional
import time

BASE_URL = "http://localhost:9000"
SESSION_ID = f"test_session_{int(time.time())}"

async def test_sse_flow():
    """Run complete SSE multi-iteration planning test."""

    print("\n" + "="*70)
    print("🚀 SSE Multi-Iteration Planning Test with Llama Analysis")
    print("="*70)

    client = httpx.AsyncClient(timeout=300.0)

    try:
        # Step 1: Generate proposal
        print("\n📋 Step 1: Generating planning proposal...")
        print(f"   Session ID: {SESSION_ID}")

        proposal_response = await client.post(
            f"{BASE_URL}/api/generate-proposal",
            json={
                "goal": "Design a comprehensive strategy for implementing AI in healthcare systems",
                "session_id": SESSION_ID
            }
        )

        if proposal_response.status_code != 200:
            print(f"   ❌ Proposal generation failed: {proposal_response.status_code}")
            print(f"   Response: {proposal_response.text[:500]}")
            return False

        proposal_data = proposal_response.json()
        proposal_text = proposal_data.get("proposal", "")
        print(f"   ✅ Proposal generated ({len(proposal_text)} chars)")
        if proposal_text:
            print(f"   Preview: {proposal_text[:200]}...")

        # Step 2: Simulate approval and execute plan with SSE
        print("\n🚀 Step 2: Executing plan with 4 iterations (checkpoint_interval=2)...")
        print("   Listening for SSE events...")

        checkpoint_count = 0
        iteration_count = 0
        events_received = []

        async with client.stream(
            "GET",
            f"{BASE_URL}/api/execute-plan",
            params={
                "goal": "Design a comprehensive strategy for implementing AI in healthcare systems",
                "proposal": proposal_text,
                "max_iterations": 4,
                "checkpoint_interval": 2,
                "session_id": SESSION_ID
            }
        ) as sse_response:
            async for line in sse_response.aiter_lines():
                if not line or not line.startswith("data: "):
                    continue

                try:
                    event_data = json.loads(line[6:])  # Remove "data: " prefix
                    event_type = event_data.get("type", "unknown")
                    events_received.append(event_type)

                    # Log event
                    if event_type == "planning_started":
                        print(f"\n   📍 Event: planning_started")
                        print(f"      Goal: {event_data.get('goal', 'N/A')[:60]}...")
                        print(f"      Max iterations: {event_data.get('max_iterations', '?')}")
                        print(f"      Checkpoint interval: {event_data.get('checkpoint_interval', '?')}")

                    elif event_type == "iteration_started":
                        iteration_count += 1
                        print(f"\n   📍 Event: iteration_started (Iteration {event_data.get('iteration', '?')} of {event_data.get('max', '?')})")

                    elif event_type == "checkpoint_reached":
                        checkpoint_count += 1
                        print(f"\n   ⏹️ Event: checkpoint_reached (Checkpoint {checkpoint_count})")
                        print(f"      Iteration: {event_data.get('iteration', '?')}")
                        print(f"      Frameworks applied: {len(event_data.get('frameworks_so_far', []))} frameworks")
                        print(f"      Data points extracted: {event_data.get('data_points_so_far', 0)} points")

                        # Check improvements analysis
                        improvements = event_data.get('improvements', {})
                        if improvements:
                            print(f"\n      🧠 Llama's Improvement Analysis:")

                            if improvements.get('is_first_checkpoint'):
                                print(f"         ✓ First Checkpoint: {improvements.get('status', 'N/A')}")
                            else:
                                imp = improvements.get('improvements', {})
                                comp = improvements.get('comparison', {})

                                if imp:
                                    print(f"         • Research Improvements: {imp.get('research_improvements', 'N/A')[:100]}...")
                                    print(f"         • Frameworks Applied: {imp.get('frameworks_applied', 'N/A')[:100]}...")
                                    print(f"         • Use Cases Found: {imp.get('use_cases_found', 'N/A')[:100]}...")
                                    print(f"         • Analytical Improvements: {imp.get('analytical_improvements', 'N/A')[:100]}...")
                                    print(f"         • Key Discovery: {imp.get('key_discovery', 'N/A')[:100]}...")
                                    print(f"         • Depth Score: {imp.get('depth_increase', 'N/A')}/10")

                                if comp:
                                    print(f"\n         Metrics:")
                                    print(f"         • New Frameworks Added: +{comp.get('frameworks_added', 0)}")
                                    print(f"         • Data Points Gained: +{comp.get('data_points_gained', 0)}")
                                    print(f"         • Depth Score: {comp.get('depth_score', 0)}/10")

                        # AUTO-APPROVE checkpoint to continue testing
                        print(f"\n      Approving checkpoint {checkpoint_count}...")
                        approval_response = await client.post(
                            f"{BASE_URL}/api/checkpoint-approval",
                            json={
                                "session_id": SESSION_ID,
                                "checkpoint": checkpoint_count
                            }
                        )

                        if approval_response.status_code == 200:
                            print(f"      ✅ Checkpoint {checkpoint_count} approved")
                        else:
                            print(f"      ❌ Checkpoint approval failed: {approval_response.status_code}")

                    elif event_type == "checkpoint_approved":
                        print(f"\n   ✅ Event: checkpoint_approved (Checkpoint {event_data.get('checkpoint', '?')})")

                    elif event_type == "final_plan":
                        plan = event_data.get('plan', '')
                        print(f"\n   ✅ Event: final_plan")
                        print(f"      Plan length: {len(plan)} characters")
                        print(f"      Frameworks: {event_data.get('frameworks', [])}")
                        print(f"      Data points: {event_data.get('data_points', 0)}")
                        print(f"      Iterations: {event_data.get('iterations', '?')}")
                        print(f"      Checkpoints: {event_data.get('checkpoints', '?')}")

                        if plan:
                            print(f"      Preview: {plan[:200]}...")

                    elif event_type == "complete":
                        print(f"\n   ✅ Event: complete (stream closed)")

                    elif event_type == "error":
                        print(f"\n   ❌ Event: error")
                        print(f"      Error: {event_data.get('error', 'Unknown error')}")

                except json.JSONDecodeError as e:
                    print(f"   ⚠️  Failed to parse event: {e}")
                    print(f"      Line: {line[:100]}")

        # Step 3: Verify flow
        print("\n" + "="*70)
        print("📊 Test Summary")
        print("="*70)
        print(f"\n✅ Events Received: {events_received}")
        print(f"\n✅ Statistics:")
        print(f"   • Total events: {len(events_received)}")
        print(f"   • Iterations run: {iteration_count}")
        print(f"   • Checkpoints reached: {checkpoint_count}")

        # Verify expected events
        expected_events = {
            "planning_started": "planning_started" in events_received,
            "iteration_started": "iteration_started" in events_received,
            "checkpoint_reached": "checkpoint_reached" in events_received,
            "checkpoint_approved": "checkpoint_approved" in events_received,
            "final_plan": "final_plan" in events_received,
            "complete": "complete" in events_received
        }

        print(f"\n✅ Event Verification:")
        all_ok = True
        for event_name, received in expected_events.items():
            status = "✅" if received else "❌"
            print(f"   {status} {event_name}: {'YES' if received else 'NO'}")
            if not received:
                all_ok = False

        # Verify checkpoint count
        print(f"\n✅ Checkpoint Count:")
        expected_checkpoints = 2  # 4 iterations with checkpoint_interval=2 = 2 checkpoints
        if checkpoint_count == expected_checkpoints:
            print(f"   ✅ Got {checkpoint_count} checkpoints (expected {expected_checkpoints})")
        else:
            print(f"   ⚠️  Got {checkpoint_count} checkpoints (expected {expected_checkpoints})")
            all_ok = False

        print("\n" + "="*70)
        if all_ok and checkpoint_count == expected_checkpoints:
            print("✅ ALL TESTS PASSED!")
            print("="*70)
            return True
        else:
            print("⚠️  SOME TESTS MAY HAVE ISSUES - Check details above")
            print("="*70)
            return False

    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False

    finally:
        await client.aclose()


if __name__ == "__main__":
    success = asyncio.run(test_sse_flow())
    sys.exit(0 if success else 1)
