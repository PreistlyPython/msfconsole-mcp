async def _send_json(self, data: Dict[str, Any]):
    """Send a JSON response to stdout."""
    try:
        # Add newline to ensure proper message separation
        json_str = json.dumps(data) + "\n"
        logger.debug(f"Sending JSON response (first 100 chars): {json_str[:100]}...")
        # In MCP, we must ensure only valid JSON is sent to stdout
        sys.stdout.write(json_str)
        sys.stdout.flush()
        logger.debug("JSON response sent and flushed")
    except Exception as e:
        logger.error(f"Error sending JSON response: {e}")
        logger.error(f"Response data: {str(data)[:200]}...")
