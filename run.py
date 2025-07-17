from mixtral_harness.harness import Harness

def main():
    """
    Initializes and runs the processing harness.
    """
    harness = Harness()
    harness.process_directory()

if __name__ == "__main__":
    main()