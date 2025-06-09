#!/usr/bin/env python3
"""
Test suite for PixelWriter to ensure array conversion optimization doesn't break functionality.
"""

import numpy as np
import socket
from unittest.mock import Mock, patch
import sys
import os

# Add the wledcast module to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'wledcast'))

from wledcast.wled.pixel_writer import PixelWriter


def test_array_conversion_equivalence():
    """Test that the new direct conversion produces identical results to the old method."""
    print("Testing array conversion equivalence...")
    
    # Test different array shapes and data types
    test_cases = [
        # Small arrays
        np.array([[[255, 0, 0], [0, 255, 0]], [[0, 0, 255], [128, 128, 128]]], dtype=np.uint8),
        # Single row
        np.array([[[100, 150, 200]]], dtype=np.uint8),
        # Different values
        np.random.randint(0, 256, size=(8, 8, 3), dtype=np.uint8),
        # Edge cases
        np.zeros((2, 2, 3), dtype=np.uint8),
        np.full((2, 2, 3), 255, dtype=np.uint8),
    ]
    
    for i, rgb_array in enumerate(test_cases):
        print(f"  Test case {i+1}: shape {rgb_array.shape}")
        
        # Old method: flatten().tolist() then bytearray()
        old_flat = rgb_array.flatten().tolist()
        old_bytes = bytearray(old_flat)
        
        # New method: flatten().tobytes()
        new_bytes = rgb_array.flatten().tobytes()
        
        # Compare results
        assert len(old_bytes) == len(new_bytes), f"Length mismatch: {len(old_bytes)} vs {len(new_bytes)}"
        assert bytes(old_bytes) == new_bytes, f"Content mismatch in test case {i+1}"
        
        print(f"    ✓ Length: {len(new_bytes)} bytes")
        print(f"    ✓ Content matches")


def test_ddp_packet_structure():
    """Test that DDP packets are correctly formed with the new conversion."""
    print("\nTesting DDP packet structure...")
    
    # Create a small test array
    rgb_array = np.array([[[255, 0, 0], [0, 255, 0]], [[0, 0, 255], [128, 128, 128]]], dtype=np.uint8)
    
    # Mock socket to capture packets
    with patch('socket.socket') as mock_socket:
        mock_socket_instance = Mock()
        mock_socket.return_value = mock_socket_instance
        
        writer = PixelWriter("192.168.1.100")
        
        # Test the new conversion method
        byte_data = rgb_array.flatten().tobytes()
        writer._send_ddp_data(byte_data)
        
        # Verify socket.sendto was called
        assert mock_socket_instance.sendto.called, "sendto should have been called"
        
        # Get the packet that was sent
        call_args = mock_socket_instance.sendto.call_args
        packet_data, address = call_args[0]
        
        print(f"    ✓ Packet sent to {address}")
        print(f"    ✓ Packet length: {len(packet_data)} bytes")
        
        # Verify DDP header structure (first 10 bytes)
        assert len(packet_data) >= 10, "Packet should have at least 10-byte header"
        
        header = packet_data[:10]
        print(f"    ✓ Header: {header.hex()}")
        
        # Verify data portion contains our RGB data
        data_portion = packet_data[10:]
        expected_data = byte_data
        assert data_portion == expected_data, "Data portion should match our RGB data"
        
        print(f"    ✓ Data portion matches (first 8 bytes): {data_portion[:8].hex()}")


def test_performance_comparison():
    """Compare performance of old vs new method."""
    print("\nTesting performance comparison...")
    
    import time
    
    # Create a realistic-sized array (32x32 RGB)
    rgb_array = np.random.randint(0, 256, size=(32, 32, 3), dtype=np.uint8)
    
    # Time old method
    start_time = time.time()
    for _ in range(1000):
        old_flat = rgb_array.flatten().tolist()
        old_bytes = bytearray(old_flat)
    old_time = time.time() - start_time
    
    # Time new method
    start_time = time.time()
    for _ in range(1000):
        new_bytes = rgb_array.flatten().tobytes()
    new_time = time.time() - start_time
    
    improvement = (old_time - new_time) / old_time * 100
    
    print(f"    Old method (1000 iterations): {old_time:.4f}s")
    print(f"    New method (1000 iterations): {new_time:.4f}s")
    print(f"    Performance improvement: {improvement:.1f}%")
    
    # Verify new method is faster
    assert new_time < old_time, "New method should be faster"
    print(f"    ✓ New method is {improvement:.1f}% faster")


def test_edge_cases():
    """Test edge cases that might cause issues."""
    print("\nTesting edge cases...")
    
    # Test with different dtypes
    test_arrays = [
        np.array([[[255, 0, 0]]], dtype=np.uint8),  # Single pixel
        np.array([[[0, 0, 0], [255, 255, 255]]], dtype=np.uint8),  # Two pixels
        np.random.randint(0, 256, size=(1, 1000, 3), dtype=np.uint8),  # Long strip
    ]
    
    for i, rgb_array in enumerate(test_arrays):
        print(f"  Edge case {i+1}: shape {rgb_array.shape}")
        
        # Ensure both methods work
        old_result = bytearray(rgb_array.flatten().tolist())
        new_result = rgb_array.flatten().tobytes()
        
        assert bytes(old_result) == new_result, f"Results differ for edge case {i+1}"
        print(f"    ✓ Conversion works correctly")


def test_integration_with_pixel_writer():
    """Test the complete integration with PixelWriter class."""
    print("\nTesting integration with PixelWriter...")
    
    with patch('socket.socket') as mock_socket:
        mock_socket_instance = Mock()
        mock_socket.return_value = mock_socket_instance
        
        writer = PixelWriter("192.168.1.100")
        
        # Test with a realistic array
        rgb_array = np.random.randint(0, 256, size=(16, 16, 3), dtype=np.uint8)
        
        # This should work without errors
        writer.update_pixels(rgb_array)
        
        # Verify the call was made
        assert mock_socket_instance.sendto.called, "Socket sendto should have been called"
        
        print("    ✓ Integration test passed")


if __name__ == "__main__":
    print("Running PixelWriter optimization tests...\n")
    
    try:
        test_array_conversion_equivalence()
        test_ddp_packet_structure()
        test_performance_comparison()
        test_edge_cases()
        test_integration_with_pixel_writer()
        
        print("\n" + "="*50)
        print("🎉 ALL TESTS PASSED!")
        print("The array conversion optimization is safe to deploy.")
        print("="*50)
        
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        print("Do not deploy the optimization until this is fixed.")
        sys.exit(1)