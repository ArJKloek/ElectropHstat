class MockLib8MosInd():
    def __init__(self):
        self.state = [0] * 8  # simulate 8 MOSFETs
        self.pwm = [0] * 8
        print("[MOCK] Initialized MockLib8MosInd")

    def set(self, stack, mosfet, value):
        self.state[mosfet] = value
        print(f"[MOCK] set(stack={stack}, mosfet={mosfet}, value={value})")

    def get(self, stack, mosfet):
        print(f"[MOCK] get(stack={stack}, mosfet={mosfet}) => {self.state[mosfet]}")
        return self.state[mosfet]

    def set_all(self, stack, value):
        val = 1 if value else 0
        self.state = [val] * 8
        print(f"[MOCK] set_all(stack={stack}, value={value})")

    def get_all(self, stack):
        result = sum((1 << i) if val else 0 for i, val in enumerate(self.state))
        print(f"[MOCK] get_all(stack={stack}) => {result}")
        return result

    def set_pwm(self, stack, mosfet, value):
        self.pwm[mosfet] = value
        print(f"[MOCK] set_pwm(stack={stack}, mosfet={mosfet}, value={value})")

    def get_pwm(self, stack, mosfet):
        print(f"[MOCK] get_pwm(stack={stack}, mosfet={mosfet}) => {self.pwm[mosfet]}")
        return self.pwm[mosfet]