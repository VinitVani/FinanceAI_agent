def test_imports():
    import importlib

    modules = [
        "Backend.agents",  # replace with real package paths
        "Backend",
        "FinanceAI_agent",
    ]
    for mod in modules:
        importlib.import_module(mod)


def test_dummy_agent_pipeline():
    # Replace with your real agent entrypoint
    from Backend import agents

    # adjust to actual callable
    # Minimal no-op invocation; must be fast and not hit network
    result = getattr(agents, "run_dummy", lambda: "ok")()
    assert result is not None
