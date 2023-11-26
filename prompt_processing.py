from utils import print_info, print_warning, print_error
from prompt_processing_utils import (
    extract_generated_prompt,
    clean_prompt,
    extract_variable_placeholders,
    extract_test_cases,
    update_variable_names,
    load_prompt,
    extract_eval_result,
    handle_eval_result,
    update_test_results,
    store_results_for_file,
    parse_results_for_file,
)

NUM_TEST_CASES = 5


class PromptProcessor:
    def __init__(self, api_client):
        self.api = api_client

    # Function to generate prompts
    def generate_prompt(self, prompt_description, failed_eval_results):
        if failed_eval_results:
            print_info(f"\n*** Updating prompt... ***")
            # If there are failed evaluation results, build string that includes them
            failed_prompt = []
            failed_inputs = []
            failed_responses = []
            failed_evaluations = []
            test_cases_and_evaluations = ""
            for i, failed_eval in enumerate(failed_eval_results):
                failed_prompt.append(failed_eval_results[failed_eval]["prompt"])
                failed_inputs.append(failed_eval_results[failed_eval]["input"])
                failed_responses.append(failed_eval_results[failed_eval]["response"])
                failed_evaluations.append(
                    failed_eval_results[failed_eval]["evaluation"]
                )
                if i == 0:
                    test_cases_and_evaluations += f"<Original_Prompt>\n{failed_eval_results[failed_eval]['prompt']}\n</Original_Prompt>\n"
                test_cases_and_evaluations += f"<Test_Case_{i+1}>\n<Input{i+1}>\n{failed_eval_results[failed_eval]['input']}\n</Input{i+1}>\n<Response_{i+1}>\n{failed_eval_results[failed_eval]['response']}\n</Response_{i+1}>\n<Evaluation_{i+1}>\n{failed_eval_results[failed_eval]['evaluation']}\n</Evaluation_{i+1}>\n</Test_Case_{i+1}>"

            prompt_generation_prompt = f"""\n\nHuman: You are an experienced prompt engineer. Your task is to improve an existing LLM prompt in order to elicit an LLM to achieve the specified goal and/or assumes the specified role. The prompt should adherence to best-practices, and produce the best possible likelihood of success. You will be provided with an existing prompt, test cases that failed, and evaluations for those test cases. You will improve the prompt to address the failed test cases and evaluations.

            Follow this procedure to generate the prompt:
            1. Read the prompt description carefully, focusing on its intent, goal, and intended functionality it is designed to elicit from the LLM. Document your understanding of the prompt description and brainstorm in <prompt_generation_scratchpad></prompt_generation_scratchpad> XML tags.
            2. Read the failed inputs, responses, and evaluations carefully. Document your understanding of the failed inputs, responses, and evaluations in <lessons_learned></lessons_learned> XML tags.
            3. Using best practices, including organizing information in XML tags when necessary, generate a new iteration of the prompt that incorporates lessons learned.
            4. Write your new prompt in <generated_prompt></generated_prompt> XML tags. The updated prompt must continue to take the same input variable(s) or text as the original prompt. Your prompt must start with '\n\nH:' and end with '\n\nA:' to ensure proper formatting.
            
            Generate a prompt based on the following prompt description. Read it carefully:
            Prompt Description: ```{prompt_description}```
            
            Here are the test cases and evaluations. Read them carefully:
            <test_cases_and_evaluations>
            {test_cases_and_evaluations}
            </test_cases_and_evaluations>
            
            Remember to put your new prompt within <generated_prompt></generated_prompt> XML tags. Think step by step and double check your prompt against the procedure and failed input(s) before it's finalized.

            Assistant: """
        else:
            print_info(f"\n*** Generating an initial prompt... ***")
            prompt_generation_prompt = f"""\n\nHuman: You are an experienced prompt engineer. Your task is to read a prompt description written by a user and craft a prompt that will successfully elicit an LLM to achieve the specified goal or task. The prompt should adherence to best-practices, and produce the best possible likelihood of success.

            Follow this procedure to generate the prompt:
            1. Read the prompt description carefully, focusing on its intent, goal, and intended functionality it is designed to elicit from the LLM. Document your understanding of the prompt description and brainstorm in <prompt_generation_scratchpad></prompt_generation_scratchpad> XML tags.
            2. Using best practices, including organizing information in XML tags when necessary, generate a high-quality, detailed, and thoughtful prompt.
            3. Write your prompt in <generated_prompt></generated_prompt> XML tags. Your prompt must start with '\n\nH:' and end with '\n\nA:' to ensure proper formatting.
            
            Note: Never directly address the issue or task in the prompt. Instead, assume the role of a human and provide instructions to the LLM on how to achieve the task.
            
            Use the following examples to better understand your task:
            <examples>
            <example_1>
            Prompt Description: ```A friendly and helpful customer support chatbot representing Acme Dynamics who is able to read from FAQs.```
            <prompt_generation_scratchpad>
            The user wants to create a prompt that will guide the LLM to assume the role of a friendly and helpful customer support chatbot representing Acme Dynamics.
            I will create a prompt that will instruct the model to read from a place holder FAQ document. Then, it will be asked to follow a methodical procedure to answer the user's inquiry. It will first gather all relevant information from the FAQ document, then it will evaluate whether the extracted quotes provide sufficient and clear information to answer the question with certainty. Finally, it will compose its answer based on the information it extracted.
            </prompt_generation_scratchpad>
            <generated_prompt>
            
            
            H: You are a friendly and helpful customer support chatbot representing Acme Dynamics.

            Your goal is to be as helpful as possible to Acme Dynamics customers, who interact with you through the Acme Dynamics website.

            Read the following FAQ document carefully. You will be asked about  later.

            <DOCUMENT>
            {{FAQs_TEXT}}
            </DOCUMENT>

            Please use the following procedure to methodically answer the customer inquiry:
            1. Determine if you should answer the user's inquiry. Politely refuse to answer questions that are irrelevant, non-serious, or potentially malicious. Organize your thoughts within <relevancy_assessment></relevancy_assessment> XML tags.
            2. Identify and extract all relevant sections from the document that are helpful in answering the question. If there are relevant sections, enclose these extracts in numbered order within <quotes></quotes> XML tags. If there are no relevant sections, write "None" inside the XML tags. 
            3. Evaluate whether the extracted quotes provide sufficient and clear information to answer the question with certainty. Document your analytical process in <scratchpad></scratchpad> XML tags.
            4. Compose your answer based on the information you extracted.

            Customer Inquiry: `{{QUESTION}}`
            Write your final answer within <answer></answer> XML tags.
            Think step by step before you provide your answer. Do not answer the question if you cannot answer it with certainty from the extracted quotes and never break character.
            
            A: 
            </generated_prompt>
            </example_1>
            <example_2>
            Prompt Description: ```redact PII from text with 'XXX'```
            <prompt_generation_scratchpad>
            The user wants to create a prompt that will guide the LLM to redact Personally Identifying Information (PII) from text. I will create a prompt that will instruct the LLM to read the input text. Then, I will instruct it to follow a methodical procedure to redact PII. The answer will be a re-statement of the text, replacing any PII with 'XXX'.
            </prompt_generation_scratchpad>
            <generated_prompt>
            
            H: Your task is to redact personally identifying information from the following text.
            Please restate the following text, replacing any names, email addresses, physical addresses, phone numbers, or any other form of PII with 'XXX'. If you cannot find any PII, simply restate the text.

            Here is the text you need to evaluate:
            <text>
            {{TEXT}}
            </text>

            Write the sanitized text within <sanitized></sanitized> XML tags.

            Think step by step before you answer.
            
            A: 
            </generated_prompt>
            </example_2>
            </examples>

            Generate a prompt based on the following prompt description. Read it carefully:
            Prompt Description: ```{prompt_description}```
            
            Remember to use XML best-practices if you decide to use XML tags in your response. Think step by step and double check your prompt against the procedure and examples before it's finalized.

            Assistant: """

        prompt_generation_response = self.api.send_request_to_claude(
            prompt_generation_prompt, temperature=0.1
        )
        if prompt_generation_response:
            generated_prompt = extract_generated_prompt(prompt_generation_response)
            A_idx = generated_prompt.find("\nA:")
            generated_prompt = generated_prompt[: A_idx + 4]
            print_info(f"*** Generated prompt. ***")
            print(f"{clean_prompt(generated_prompt)}")
            return generated_prompt
        else:
            return "prompt generation failed."

    # Function to generate a prompt based on the goal and test results and then clean it
    def generate_and_clean_prompt(self, goal, test_results):
        prompt_template = self.generate_prompt(goal, test_results)
        cleaned_prompt_template = clean_prompt(prompt_template)
        return prompt_template, cleaned_prompt_template

    # Function to identify variable placeholders in the prompt Claude generated
    def identify_placeholders(self, prompt):
        placeholder_identification_prompt = f"""\n\nHuman: Please follow these steps to extract any variable placeholders in the text:

        1. Carefully read the text within the <text> tags.
        2. Look for variable placeholders, which are usually surrounded by curly braces. 
        3. Extract the text between the curly braces. 
        4. Make a list containing each unique variable placeholder name you found.
        5. Put the list of placeholder names within <placeholders> XML tags.
        
        If there are no variable placeholders, write "None" inside the XML tags.

        Use the following examples to strengthen your understanding of the task:
        <examples>
        <example>
        <text>
        Hello, my name is {{NAME}}. I am {{AGE}} years old.
        </text>

        <placeholders>
        {{NAME}}
        {{AGE}}
        </placeholders>
        </example>
        <example>
        <text>
        Please read the following document carefully. You will be asked about it later.
        <doc>
        {{FAQ_document}}
        </doc>
        </text>
        
        <placeholders>
        {{FAQ_document}}
        </placeholders>
        </example>
        <example>
        <text>
        Please read the following text carefully. You will be asked questions about it later.
        <text>
        {{TEXT}}
        </text>
        </text>
        
        <placeholders>
        {{TEXT}}
        </placeholders>
        </example>
        </examples>

        Here is the text you need to process. Read it carefully:
        <text>
        {prompt}
        </text>
        
        Think step by step before you answer.

        Assistant: """

        placeholder_identification_response = self.api.send_request_to_claude(
            placeholder_identification_prompt, temperature=0
        )
        if placeholder_identification_response:
            return extract_variable_placeholders(placeholder_identification_response)
        else:
            return "variable placeholder identification failed."

    # Function to generate test cases
    def generate_test_cases(self, prompt, var_names):
        print_info(f"\n*** Generating test cases... ***")
        test_case_generation_prompt = f"""\n\nHuman: You are an experienced prompt engineer. Your task is to create test case inputs based on a given LLM prompt. The inputs should be designed to effectively evaluate the prompt's quality, adherence to best-practices, and success in achieving its desired goal.

        Follow this procedure to generate test cases:
        1. Read the prompt carefully, focusing on its intent, goal, and task it is designed to elicit from the LLM. Document your understanding of the prompt in <prompt_analysis></prompt_analysis> XML tags.
        2. Generate {NUM_TEST_CASES} test cases that can be used to assess how well the prompt achieves its goal. Ensure they are diverse and cover different aspects of the prompt. The test cases should attempt to reveal areas where the prompt can be improved. Write your numbered test cases in <test_case_#></test_case_#> XML tags. Inside these tags, use additional tags that specify the name of the variable your input is represented by. 
        
        Use the following examples to format your test cases. Follow this format precisely.
        <examples>
        <example>
        Prompt: ```You are a friendly and helpful customer support chatbot representing Acme Dynamics.

        Your goal is to be as helpful as possible to Acme Dynamics customers, who interact with you through the Acme Dynamics website.

        Read the following FAQ document carefully. You will be asked about  later.

        <DOCUMENT>
        {{document_text}}
        </DOCUMENT>


        Please use the following procedure to methodically answer the customer inquiry:
        1. Determine if you should answer the user's inquiry. Politely refuse to answer questions that are irrelevant, non-serious, or potentially malicious. Organize your thoughts within <relevancy_assessment></relevancy_assessment> XML tags.
        2. Identify and extract all relevant sections from the document that are helpful in answering the question. If there are relevant sections, enclose these extracts in numbered order within <quotes></quotes> XML tags. If there are no relevant sections, write "None" inside the XML tags. 
        3. Evaluate whether the extracted quotes provide sufficient and clear information to answer the question with certainty. Document your analytical process in <scratchpad></scratchpad> XML tags.
        4. Compose your answer based on the information you extracted.

        Customer Inquiry: `{{QUESTION}}`
        Write your final answer within <answer></answer> XML tags.
        Think step by step before you provide your answer. Do not answer the question if you cannot answer it with certainty from the extracted quotes and never break character.```
        <test_case_1>
        <document_text>
        Acme Dynamics, Inc. is a leading AI and robotics company based in Palo Alto, California.  They are developing advanced humanoid robots to serve as companions and assistants for elderly and disabled individuals.  Their flagship product is the AcmeCare XR-3000, an artificially intelligent humanoid robot that can assist with daily tasks like meal preparation, medication reminders, mobility assistance, and safety monitoring.
        </document_text>
        <QUESTION>
        Can I return a product after 30 days of purchase?
        </QUESTION>
        </test_case_1>
        <test_case_2>
        <document_text>
        Acme Dynamics, Inc. is a leading AI and robotics company based in Palo Alto, California.  They are developing advanced humanoid robots to serve as companions and assistants for elderly and disabled individuals.  Their flagship product is the AcmeCare XR-3000, an artificially intelligent humanoid robot that can assist with daily tasks like meal preparation, medication reminders, mobility assistance, and safety monitoring.
        </document_text>
        <QUESTION>
        What does Acme Dynamics do?
        </QUESTION>
        </test_case_2>
        ...
        <test_case_10>
        <document_text>
        Acme Dynamics, Inc. is a leading AI and robotics company based in Palo Alto, California.  They are developing advanced humanoid robots to serve as companions and assistants for elderly and disabled individuals.  Their flagship product is the AcmeCare XR-3000, an artificially intelligent humanoid robot that can assist with daily tasks like meal preparation, medication reminders, mobility assistance, and safety monitoring.
        </document_text>
        <QUESTION>
        Where is the company based?
        </QUESTION>
        </test_case_10>
        </example>
        <example>
        Prompt: ```I will provide you with a text inside <text> XML tags. Read through the text carefully and identify all full names that include both first and last names. 

        Extract just the first and last names into a list format, with each full name on a separate line inside <names> XML tags. Only include the first and last names - do not include any other information from the text.

        Here is the text:

        <text>
        {{TEXT}} 
        </text>

        Please provide the list of extracted names here:

        <names>

        </names>

        Think step-by-step and double check your work. Do not include anything other than the first and last names extracted from the provided text.```
        <test_case_1>
        <TEXT>
        Steve Jobs was a key member of Apple, especially in its early days, and Tim Cook is the current CEO. 
        </TEXT>
        </test_case_1>
        <test_case_2>
        <TEXT>
        Mr. Jones and his student, Tim Smith, are working on a new project together.
        </TEXT>
        </test_case_2>
        ...
        <test_case_10>
        <TEXT>
        I want to know the names of all the people who work at Acme Dynamics.
        </TEXT>
        </test_case_10>
        </example>
        </examples>

        Here is the prompt for which you need to generate test cases. Read it carefully:
        <prompt_to_generate_test_cases_for>
        {prompt}
        </prompt_to_generate_test_cases_for>
        
        Here are the suggested variable names for the input(s) to the prompt. Read them carefully:
        <variable_names>
        {var_names}
        </variable_names>
        
        Remember to match the format of the example exactly. Ensure the XML tags you use match the variable name(s) in the prompt exactly. For example, if the prompt contains <text>{{TEXT}}</text>, your test input must be written within <TEXT></TEXT> XML tags. 
        
        Double check your test cases against the procedure and examples before you answer.

        Assistant: """

        test_cases_response = self.api.send_request_to_claude(
            test_case_generation_prompt, temperature=0.2
        )
        if test_cases_response:
            test_cases = extract_test_cases(test_cases_response)
            print_info(f"*** Generated {len(test_cases)} test cases. ***")
            return test_cases
        else:
            return "test case generation failed."

    # Function to set up test cases based on the prompt template and placeholder names
    def setup_test_cases(self, prompt_template, placeholder_names):
        while True:
            test_cases = self.generate_test_cases(prompt_template, placeholder_names)
            test_cases, test_case_retry = update_variable_names(
                test_cases, placeholder_names
            )
            if not test_case_retry:
                break
        return test_cases

    # Function to evaluate Claude's response
    def evaluate_response(self, prompt_to_eval, response_to_eval):
        evaluation_prompt = f"""\n\nHuman: Your task is to evaluate the adherence of a response to the associated prompt. Failure of the response to adhere perfectly to the instructions in the prompt can indicate flawed prompt engineering.
        
        Here is the prompt you need to evaluate. Read it carefully:
        <prompt_to_eval>
        {prompt_to_eval}
        </prompt_to_eval>
        
        Here is the response you need to evaluate. Read it carefully:
        <response_to_eval>
        {response_to_eval}
        </response_to_eval>

        Follow this procedure to perform your evaluation:
        1. Read the prompt carefully, focusing on its intent, format, and the specific task it is designed to elicit from the LLM.
        2. Carefully assess the response's adherence to the prompt. Clearly document your step by step analytical process, including any deviations, hallucinations, logic/reasoning mistakes or any other undesired behavior, however minor, from the prompt's specified instructions in <evaluation_scratchpad></evaluation_scratchpad> XML tags.
        3. Score the prompt's performance in generating the expected response. Mark it as 'PASS' if the response aligns perfectly with the instructions and the LLM behaves optimally. Mark it as 'FAIL' otherwise. Write your determination in <evaluation_result></evaluation_result> XML tags.

        Remember, the prompt you are evaluating was asked of another LLM, and the response was created by that same other LLM. Your job is to evaluate the performance. Think step by step before you answer.
        
        Assistant: 
        """

        evaluation_response = self.api.send_request_to_claude(
            evaluation_prompt, temperature=0
        )
        if evaluation_response:
            return evaluation_response
        else:
            return "Evaluation failed."

    # Function to send a request with the prompt to Claude and receive a response
    def execute_prompt(self, prompt):
        response = self.api.send_request_to_claude(
            prompt, temperature=0
        )
        evaluation = self.evaluate_response(prompt, response)
        return response, evaluation

    # Function to handle each test case: executing the prompt and processing the response
    def handle_test_case(self, test_case_data, prompt_template):
        skip_test_case = False
        for val in test_case_data.values():
            if val is None or val == "None":
                print_warning(f"Skipping test case because it contains invalid input.")
                skip_test_case = True
                break

        if skip_test_case:
            return True, None, None

        loaded_prompt = load_prompt(prompt_template, test_case_data)
        loaded_prompt = clean_prompt(loaded_prompt)
        response, evaluation = self.execute_prompt(loaded_prompt)
        return False, response, evaluation

    # This function processes the test cases, evaluates responses, and stores results.
    def process_test_cases(
        self, test_cases, prompt_template, combined_results, test_results
    ):
        results, failed_test_cases = {}, False
        print_info(f"\n*** Evaluating test cases... ***")
        for test_case in test_cases:
            print(f"\n{test_case} input(s): ")
            for key, val in test_cases[test_case].items():
                print_info(f"{key}: {val}")

            skip_test_case, response, evaluation = self.handle_test_case(
                test_cases[test_case], prompt_template
            )
            print(f"{test_case} response: ")
            print_info(f"{response}")
            if skip_test_case:
                continue

            eval_result = extract_eval_result(evaluation)
            test_case_failed = handle_eval_result(test_case, eval_result)
            failed_test_cases = (
                failed_test_cases or test_case_failed
            )  # Update only if a failure is detected

            test_result = update_test_results(
                test_case,
                prompt_template,
                test_cases[test_case],
                response,
                evaluation,
            )
            test_results.update(test_result)

            result_for_file = store_results_for_file(test_case, response, evaluation)
            results.update(result_for_file)

            parsed_results = parse_results_for_file(
                results, test_case, prompt_template, response
            )
            combined_results.append(parsed_results)

        return test_results, combined_results, failed_test_cases

    # Function to handle the case where no input variables are detected in the prompt
    def process_no_input_var_case(
        self, prompt_template, combined_results, test_results
    ):
        results = {}
        prompt = clean_prompt(prompt_template)
        response, evaluation = self.execute_prompt(prompt)
        eval_result = extract_eval_result(evaluation)
        eval_failed = handle_eval_result("", eval_result)
        test_results = update_test_results(0, prompt, "None", response, evaluation)
        result_for_file = store_results_for_file(0, response, evaluation)
        results.update(result_for_file)
        parsed_results = parse_results_for_file(results, 0, prompt, response)
        combined_results.append(parsed_results)
        return test_results, combined_results, eval_failed
