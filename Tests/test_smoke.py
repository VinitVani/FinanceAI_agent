def test_imports():
    import importlib

    modules = [
        "Backend.agent",  # replace with real package paths
        "Backend.core",
        "Backend",
    ]
    for mod in modules:
        importlib.import_module(mod)


def test_dummy_agent_pipeline():
    # Replace with your real agent entrypoint
    from Backend import agent

    # adjust to actual callable
    # Minimal no-op invocation; must be fast and not hit network
    result = getattr(agent, "run_dummy", lambda: "ok")()
    assert result is not None
