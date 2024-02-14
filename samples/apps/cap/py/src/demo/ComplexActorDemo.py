from LocalActorNetwork import LocalActorNetwork
from demo.AppAgents import FidelityAgent, FinancialPlannerAgent, PersonalAssistant, QuantAgent, UserInterfaceAgent
from termcolor import colored
import time

def complex_actor_demo():
    """
    This function demonstrates the usage of a complex actor system.
    It creates a local actor network, registers various agents,
    connects them, and interacts with a personal assistant agent.
    The function continuously prompts the user for input messages,
    sends them to the personal assistant agent, and terminates
    when the user enters "quit".
    """
    network = LocalActorNetwork()
    # Register agents

    network.register(PersonalAssistant())
    network.register(UserInterfaceAgent())
    network.register(FidelityAgent())
    network.register(FinancialPlannerAgent())
    network.register(QuantAgent())
    # Tell agents to connect to other agents

    network.connect()
    # Get a channel to the personal assistant agent

    pa = network.lookup_agent(PersonalAssistant.cls_agent_name)
    while True:
        time.sleep(0.1)  # Let the network do things
        # Get a message from the user

        msg = input(colored("Enter a message: ", "light_red"))
        # Send the message to the personal assistant agent

        pa.send_txt_msg(msg)
        if msg.lower() == "quit":
            break
    # Cleanup

    pa.close()
    network.disconnect()