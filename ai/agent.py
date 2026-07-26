from typing import Optional
from models.building_state import BuildingState
from models.optimization_context import OptimizationContext
from ai.prompt_builder import (
    load_system_prompt,
    build_user_prompt_sections
)
from ai.llm_client import LLMClient
from ai.decision_schema import Decision
from utils.logger import IterationLogger


class BuildingOptimizationAgent:

    def __init__(self):
        self.llm = LLMClient()
        self.system_prompt = load_system_prompt()

    def decide(
        self,
        state: BuildingState,
        candidates: list,
        context: Optional[OptimizationContext] = None,
        iteration: Optional[int] = None,
        logger: Optional[IterationLogger] = None,
        debug: bool = False
    ) -> Decision:

        user_prompt, prompt_sections = build_user_prompt_sections(state, candidates, context)

        if debug:
            print("\n==========================")
            print("Building State")
            print("==========================")
            print(state)
            print("\n==========================")
            print("Prompt Sent To LLM")
            print("==========================")
            print(user_prompt)

        llm_output = self.llm.generate_decision_with_metadata(
            self.system_prompt,
            user_prompt,
            context=context
        )

        decision: Decision = llm_output["decision"]
        raw_content: str = llm_output["raw_content"]

        if debug:
            print("\n==========================")
            print("LLM Raw Response")
            print("==========================")
            print(raw_content)
            print("\n==========================")
            print("Parsed Decision")
            print("==========================")
            print(f"Selected Candidate Index: {decision.selected_candidate_index}")
            print(f"Reason           : {decision.reason}")
            print(f"Confidence       : {decision.confidence}")

        if logger is not None and iteration is not None:
            metadata = {
                "response_time_ms": llm_output.get("response_time_ms", 0),
                "model": llm_output.get("model", "llama-3.3-70b-versatile"),
            }
            if "usage" in llm_output and llm_output["usage"]:
                metadata.update(llm_output["usage"])

            logger.log_iteration(
                iteration=iteration,
                building_state=state,
                prompt=user_prompt,
                prompt_sections=prompt_sections,
                raw_response=raw_content,
                decision=decision,
                system_prompt=self.system_prompt,
                metadata=metadata
            )

        return decision