from enum import Enum
import re
from typing import List

class ConversationStage(Enum):
    GREETING = "greeting"
    QUALIFICATION = "qualification_questions"
    PITCHING = "pitching"
    CLOSING = "closing"

class StageManager:
    def __init__(self):
        self.current_stage = ConversationStage.QUALIFICATION
        self.qualification_count = 0
        self.required_qualifications = 1
        
        self.stage_triggers = {
            ConversationStage.GREETING: [
                r'\bhi\b|\bhello\b|\bhey\b|\byes\b',
                r'\b(good\s+(morning|afternoon|evening))\b',
                r'\bnamaste\b|\bgreetings\b'
            ],
            ConversationStage.QUALIFICATION: [
                r'\bwhat\b|\bwhere\b|\bwhen\b|\bhow\b|\bwhy\b',
                r'\binterested\b|\blooking\s+for\b|\bneed\b',
                r'\bexperience\b|\bbackground\b|\bgoals\b'
            ],
            ConversationStage.PITCHING: [
                r'\bprice\b|\bcost\b|\bfees\b',
                r'\bdetails\b|\bmore\s+information\b',
                r'\bbenefits\b|\bfeatures\b|\badvantages\b',
                r'\bcourse\b|\bprogram\b|\btraining\b'
            ],
            ConversationStage.CLOSING: [
                r'\bbuy\b|\bpurchase\b|\benroll\b',
                r'\bsign\s+up\b|\bregister\b',
                r'\bproceed\b|\bagree\b|\bjoin\b'
            ]
        }
        
        # Additional patterns for stage progression
        self.progression_signals = {
            ConversationStage.QUALIFICATION: [
                r'\byes\b|\bsure\b|\binterested\b|\btell\s+me\s+more\b',
                r'\bhow\s+much\b|\bwhat\'s\s+the\s+cost\b',
                r'\bcan\s+you\s+explain\b|\btell\s+me\s+about\b'
            ]
        }
    
    def get_current_stage(self) -> str:
        return self.current_stage.value
    
    def analyze_response(self, customer_response: str, patterns: List[str]) -> bool:
        response_lower = customer_response.lower()
        return any(re.search(pattern, response_lower) for pattern in patterns)
    
    def should_progress_from_qualification(self, customer_response: str) -> bool:
        if self.analyze_response(customer_response, self.progression_signals[ConversationStage.QUALIFICATION]):
            return True
        
        if self.analyze_response(customer_response, self.stage_triggers[ConversationStage.PITCHING]):
            return True
        
        self.qualification_count += 1
        return self.qualification_count >= self.required_qualifications
    
    def update_stage(self, customer_response: str) -> str:
        if self.current_stage == ConversationStage.QUALIFICATION:
            if self.should_progress_from_qualification(customer_response):
                self.current_stage = ConversationStage.PITCHING
                return self.current_stage.value
        
        elif self.current_stage == ConversationStage.GREETING:
            if self.analyze_response(customer_response, self.stage_triggers[ConversationStage.GREETING]):
                self.current_stage = ConversationStage.QUALIFICATION
        
        elif self.current_stage == ConversationStage.PITCHING:
            if self.analyze_response(customer_response, self.stage_triggers[ConversationStage.CLOSING]):
                self.current_stage = ConversationStage.CLOSING
        
        print(f"Stage updated to: {self.current_stage.value}, Qualification count: {self.qualification_count}")
        
        return self.current_stage.value
    
    def reset(self):
        self.current_stage = ConversationStage.GREETING
        self.qualification_count = 0