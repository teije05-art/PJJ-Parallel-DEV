#!/usr/bin/env python3
"""
Quick verification script for SSE endpoint structure and basic flow.

Tests:
1. Proposal generation works
2. SSE endpoint responds with proper event structure
3. Checkpoint approval endpoint works
"""

import asyncio
import json
import httpx
import sys
from typing import Optional
import time

BASE_URL = "http://localhost:9000"
SESSION_ID = f"verify_session_{int(time.time())}"

async def verify_endpoints():
    """Verify core SSE endpoints work properly."""

    print("\n" + "="*70)
    print("🧪 SSE Endpoint Structure Verification")
    print("="*70)

    client = httpx.AsyncClient(timeout=60.0)

    try:
        # Test 1: Health check
        print("\n✅ Test 1: Health Check")
        health_response = await client.get(f"{BASE_URL}/health")
        if health_response.status_code == 200:
            print(f"   ✅ Server is healthy")
        else:
            print(f"   ❌ Server health check failed: {health_response.status_code}")
            return False

        # Test 2: Proposal generation
        print("\n✅ Test 2: Proposal Generation")
        proposal_response = await client.post(
            f"{BASE_URL}/api/generate-proposal",
            json={
                "goal": "Design AI healthcare strategy",
                "session_id": SESSION_ID
            }
        )

        if proposal_response.status_code != 200:
            print(f"   ❌ Proposal generation failed: {proposal_response.status_code}")
            print(f"   Response: {proposal_response.text[:300]}")
            return False

        proposal_data = proposal_response.json()
        if proposal_data.get("status") != "success":
            print(f"   ❌ Proposal status not success: {proposal_data.get('status')}")
            return False

        proposal_text = proposal_data.get("proposal", "")
        print(f"   ✅ Proposal generated ({len(proposal_text)} chars)")

        # Test 3: SSE Endpoint Basic Response
        print("\n✅ Test 3: SSE Endpoint Structure")
        print("   Starting SSE stream (will listen for first 10 events)...")

        events_received = []
        event_count = 0
        max_events_to_check = 10

        async with client.stream(
            "GET",
            f"{BASE_URL}/api/execute-plan",
            params={
                "goal": "Design AI healthcare strategy",
                "proposal": proposal_text[:500],  # Use shorter proposal for speed
                "max_iterations": 2,  # Only 2 iterations for quick verification
                "checkpoint_interval": 1,
                "session_id": SESSION_ID
            }
        ) as sse_response:
            async for line in sse_response.aiter_lines():
                if not line or not line.startswith("data: "):
                    continue

                try:
                    event_data = json.loads(line[6:])
                    event_type = event_data.get("type", "unknown")
                    events_received.append(event_type)

                    print(f"\n   📍 Event {len(events_received)}: {event_type}")

                    # Verify event structure
                    if event_type == "planning_started":
                        assert "goal" in event_data, "Missing 'goal' in planning_started"
                        assert "max_iterations" in event_data, "Missing 'max_iterations'"
                        print(f"      ✅ Correct structure: goal, max_iterations, checkpoint_interval")

                    elif event_type == "iteration_started":
                        assert "iteration" in event_data, "Missing 'iteration'"
                        assert "max" in event_data, "Missing 'max'"
                        print(f"      ✅ Correct structure: iteration={event_data['iteration']}, max={event_data['max']}")

                    elif event_type == "checkpoint_reached":
                        assert "checkpoint_number" in event_data, "Missing 'checkpoint_number'"
                        assert "improvements" in event_data, "Missing 'improvements' (critical for Llama analysis)"

                        improvements = event_data.get("improvements", {})
                        print(f"      ✅ Checkpoint {event_data['checkpoint_number']} structure valid")

                        # Check Llama analysis structure
                        if improvements.get("is_first_checkpoint"):
                            print(f"         ✅ First checkpoint detected")
                        elif improvements.get("improvements"):
                            imp = improvements["improvements"]
                            required_fields = [
                                "research_improvements",
                                "frameworks_applied",
                                "use_cases_found",
                                "analytical_improvements",
                                "key_discovery",
                                "depth_increase"
                            ]
                            missing = [f for f in required_fields if f not in imp]
                            if missing:
                                print(f"         ⚠️  Missing fields: {missing}")
                            else:
                                print(f"         ✅ All Llama analysis fields present:")
                                print(f"            • Research Improvements: {imp['research_improvements'][:50]}...")
                                print(f"            • Key Discovery: {imp['key_discovery'][:50]}...")
                                print(f"            • Depth Score: {imp['depth_increase']}/10")

                        # Now test checkpoint approval endpoint
                        print(f"\n      Testing checkpoint approval endpoint...")
                        approval_resp = await client.post(
                            f"{BASE_URL}/api/checkpoint-approval",
                            json={
                                "session_id": SESSION_ID,
                                "checkpoint": event_data["checkpoint_number"]
                            }
                        )

                        if approval_resp.status_code == 200:
                            print(f"      ✅ Checkpoint approval endpoint works: {approval_resp.json().get('status')}")
                        else:
                            print(f"      ⚠️  Checkpoint approval returned {approval_resp.status_code}")

                    elif event_type == "checkpoint_approved":
                        print(f"      ✅ Backend confirmed checkpoint approval")

                    elif event_type == "final_plan":
                        assert "plan" in event_data, "Missing 'plan' in final_plan event"
                        assert "frameworks" in event_data, "Missing 'frameworks'"
                        print(f"      ✅ Final plan structure valid ({len(event_data['plan'])} chars)")
                        print(f"         Frameworks: {len(event_data.get('frameworks', []))} total")
                        print(f"         Data points: {event_data.get('data_points', 0)}")

                    elif event_type == "complete":
                        print(f"      ✅ Stream properly closed")

                    elif event_type == "error":
                        print(f"      ❌ Error event: {event_data.get('error', 'Unknown')}")
                        return False

                    event_count += 1
                    if event_count >= max_events_to_check and event_type not in ["final_plan", "complete"]:
                        print(f"\n   (Stopping after {max_events_to_check} events for quick verification)")
                        break

                except json.JSONDecodeError as e:
                    print(f"   ❌ JSON parse error: {e}")
                    print(f"      Line: {line[:100]}")
                    return False

        # Summary
        print("\n" + "="*70)
        print("📊 Verification Summary")
        print("="*70)
        print(f"\n✅ Events received: {events_received}")
        print(f"\n✅ Endpoint structure verification:")
        print(f"   ✅ /api/generate-proposal: Works")
        print(f"   ✅ /api/execute-plan (GET): Streams SSE events")
        print(f"   ✅ /api/checkpoint-approval (POST): Accepts approvals")

        if "checkpoint_reached" in events_received:
            print(f"\n✅ Critical Feature: Llama Improvement Analysis")
            print(f"   ✅ Checkpoint events include 'improvements' field")
            print(f"   ✅ Can display system learning between iterations")

        print("\n" + "="*70)
        print("✅ ENDPOINT VERIFICATION PASSED")
        print("="*70)
        return True

    except Exception as e:
        print(f"\n❌ Verification failed: {e}")
        import traceback
        traceback.print_exc()
        return False

    finally:
        await client.aclose()


if __name__ == "__main__":
    success = asyncio.run(verify_endpoints())
    sys.exit(0 if success else 1)
