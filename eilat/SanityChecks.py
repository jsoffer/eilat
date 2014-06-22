def check_libraries():
    try:
        import PyQt4
    except ImportError:
        print("PyQt4 is not available")
        raise
