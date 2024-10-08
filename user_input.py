from utils import print_info, print_success, print_warning


def prompt_user():
    """
    Prompts the user to choose between entering a custom prompt description or viewing preset examples.

    Returns:
        str: The generated prompt description based on user's choice.
    """
    print_warning("\n\n\n*** Prompt Generator ***")
    print_warning("\nThis tool can help engineer effective prompts.")
    print_success("\nWould you like to:")
    print("1. Enter a custom prompt description")
    print("2. View preset examples")

    user_choice = input("\nEnter your choice (1 or 2): ")

    if user_choice == "1":
        print_info("\nHere are a few examples to inspire you:")
        display_example_prompts()
        print_info(f"\nInclude any input variables the model should consider\n")
        custom_prompt = input("This prompt should guide the LLM to: ")
        print_success(f"\nCustom prompt description entered: {custom_prompt}")
        return "The prompt should guide the LLM to: " + custom_prompt
    elif user_choice == "2":
        return display_presets()
    else:
        print_warning("\nInvalid choice. Please enter 1 or 2.")
        return prompt_user()  # Recursive call for invalid input


def display_presets():
    """
    Displays a list of preset examples and prompts the user to select one.

    Returns:
        str: The selected prompt option.
    """
    pass
    prompt_options = get_prompt_options()
    print_success("\nSelect a preset example:")
    for key, value in prompt_options.items():
        print(f"{key}. {value}")
    user_input = input("\nEnter the number of your choice: ")

    if user_input in prompt_options:
        print_success(f"\nYou have selected: {prompt_options[user_input]}")
        return "The prompt should guide the LLM to: " + prompt_options[user_input]
    else:
        print_warning("\nInvalid selection. Please try again.")
        return display_presets()  # Recursive call for invalid input


def display_example_prompts():
    """
    Display a list of example prompts.

    This function prints a list of example prompts, each starting with a hyphen ("-").
    The example prompts are predefined and stored in the `example_prompts` list.

    Example prompts:
    - Identify and list key points from an input meeting transcript.
    - Rewrite an email to be more formal. Take the email as input.
    - Extract dates and event names from an input text about historical events and store them in XML tags.
    """
    example_prompts = [
        "Identify and list key points from an input meeting transcript.",
        "Rewrite an email to be more formal. Take the email as input.",
        "Extract dates and event names from an input text about historical events and store them in XML tags.",
    ]
    for example in example_prompts:
        print(f"- {example}")


def get_prompt_options():
    """
    Returns a dictionary of prompt options.

    Returns:
        dict: A dictionary where the keys are numbers representing the prompt options, and the values are the descriptions of each option.
    """
    return {
        "1": "Redact personally identifiable information from an input text with 'XXX'.",
        "2": "Solve the input reasoning question.",
        "3": "Extract phone numbers from an input text and list them in a standard format.",
        "4": "Extract and list all last names from a given input text.",
        "5": "Act as a helpful chatbot for home-office IT issues. Answer user questions using LLM general knowledge. Take a user question as input.",
        "6": "Act as a virtual customer service agent for Writer.com with access to an FAQ document. Take a user question as input.",
        "7": "Extract information from a student info text file into JSON with keys 'name', 'grade', 'gpa', 'major'.",
    }


def get_provider():
    """Prompts the user to select LLM provider, Anthropic or Writer.

    Returns:
        str: The selected provider.
    """
    while True:
        print_success("\nSelect the LLM provider:")
        print_info(
            "Note: You will need an API key for the selected provider in a .env file.\n"
        )
        print("1. Anthropic")
        print("2. Writer")
        user_input = input("\nEnter the number of your choice: ")

        if user_input == "1":
            return "Anthropic"
        elif user_input == "2":
            return "Writer"
        else:
            print_info("\nInvalid selection. Please try again.")


def get_test_cases_count():
    """
    Prompts the user to enter the number of test cases to generate.

    Returns:
        int: The number of test cases entered by the user.

    Raises:
        ValueError: If the user enters an invalid input (not a number).
    """
    while True:
        try:
            count = int(input("\nEnter the number of test cases to generate (0-5): "))
            if 0 <= count <= 5:
                return count
            else:
                print_warning("Please enter a number between 0 and 5.")
        except ValueError:
            print_warning("Invalid input. Please enter a number.")
