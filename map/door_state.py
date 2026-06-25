class DoorState:
    OPEN = "open"
    CLOSING = "closing"
    CLOSED = "closed"
    OPENING = "opening"


class DoorStateMachine:
    ANIMATION_SPEED = 3

    def __init__(self):
        self.state = DoorState.OPEN
        self.anim_frame = 0
        self.anim_counter = 0

    def start_closing(self, frame_count):
        if self.state == DoorState.CLOSED:
            return False
        self.state = DoorState.CLOSING
        self.anim_frame = frame_count - 1
        self.anim_counter = 0
        return True

    def start_opening(self):
        if self.state == DoorState.OPEN:
            return False
        self.state = DoorState.OPENING
        self.anim_frame = 0
        self.anim_counter = 0
        return True

    def update(self, frame_count):
        if self.state == DoorState.CLOSING:
            self.anim_counter += 1
            if self.anim_counter >= self.ANIMATION_SPEED:
                self.anim_counter = 0
                self.anim_frame -= 1
                if self.anim_frame <= 0:
                    self.anim_frame = 0
                    self.state = DoorState.CLOSED
                    return "closed"
                return "animating"

        elif self.state == DoorState.OPENING:
            self.anim_counter += 1
            if self.anim_counter >= self.ANIMATION_SPEED:
                self.anim_counter = 0
                self.anim_frame += 1
                if self.anim_frame >= frame_count - 1:
                    self.anim_frame = frame_count - 1
                    self.state = DoorState.OPEN
                    return "opened"
                return "animating"

        return None
