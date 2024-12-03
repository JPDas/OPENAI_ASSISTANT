import time
import json
import openai

from search_api import get_relevant_chunks
from dotenv import load_dotenv

load_dotenv()

class AssistantManager:
    def __init__(self, model, assistant_id=None, thread_id=None) -> None:
        self.client = openai.OpenAI()
        self.model = model
        self.assistant_id = assistant_id
        self.assistant = None
        if self.assistant_id:
            self.assistant = self.client.beta.assistants.retrieve(assistant_id=self.assistant_id)
                    
        self.thread = None
        self.thread_id = thread_id
        if self.thread_id:
            self.thread = self.client.beta.threads.retrieve(thread_id=self.thread_id)
        
        self.run = None
        self.summary = None

    def create_assistant(self, name, instructions, tools):
        if not self.assistant:
            self.assistant = self.client.beta.assistants.create(name=name, 
                                                                instructions=instructions, 
                                                                tools=tools, 
                                                                model=self.model)
            
            self.assistant_id = self.assistant.id

        return self.assistant_id
    
    def create_thread(self):

        if not self.thread:
            print("Creating thread")
            self.thread = self.client.beta.threads.create()

            self.thread_id = self.thread.id

        return self.thread_id
    
    def add_message_to_thread(self, role, content):
        message = None
        if self.thread:
            # add the user's message to the existing thread
            message = self.client.beta.threads.messages.create(thread_id=self.thread_id,
                                                     role=role,
                                                     content=content)
            
        return message

    def run_assistant(self, instructions):
        if self.thread and self.assistant:
            self.run = self.client.beta.threads.runs.create(thread_id=self.thread_id,
                                                            assistant_id=self.assistant_id,
                                                            instructions=instructions)
            print("Run ID:", self.run.id)
            
    def process_message(self):
        if self.thread:
            messages = self.client.beta.threads.messages.list(thread_id=self.thread_id)

            summary = []

            last_message = messages.data[0]

            response = last_message.content[0].text.value
            role = last_message.role
            summary.append(response)

            self.summary = "\n".join(summary)

            print(f"Summary---->{role.capitalize()}------>{response}")

            return response

    def call_required_functions(self, required_actions):
        if not self.run:
            return
        
        print(f"calling required functions {required_actions}")
        tools_outputs = []
        for action in required_actions["tool_calls"]:
            func_name = action["function"]["name"]
            print(func_name)

            arguments = json.load(action["function"]["arguments"])
            print(arguments)
            if func_name == "get_relevant_chunks":

                output = get_relevant_chunks(query = arguments["query"])

                print(output)

                final_string = ""
                for item in output:
                    final_string += " ".join(item)

                tools_outputs.append({"tool_call_id": action["id"], "output": final_string})

                print(f"TOOLS OUTPUT: {tools_outputs}")
            else:
                raise ValueError(f"Unknown {func_name}")
        
        return tools_outputs

    def run_steps(self):
        run_steps = self.client.beta.threads.runs.steps.list(thread_id=self.thread_id)

        print(run_steps.data)


    def wait_for_completion(self):
        if self.thread and self.run:

            while self.run.status == "queued" or self.run.status == "in_progress":
                print("Inprogress")
                self.run = self.client.beta.threads.runs.retrieve(thread_id=self.thread.id, run_id=self.run.id)
                time.sleep(1)
            
            print(self.run.model_dump_json())
            if self.run.status == "requires_action":
                tool_outputs = self.call_required_functions(required_actions = self.run.required_action.submit_tool_outputs.model_dump())

                self.run = self.client.beta.threads.runs.submit_tool_outputs(thread_id=self.thread.id, run_id=self.run.id, tool_outputs=tool_outputs)
                self.wait_for_completion()
            
            elif self.run.status == 'completed':
                response = self.process_message()

                return response
                
                    



