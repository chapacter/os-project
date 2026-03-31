import pymunk
import pymunk.pygame_util

COLLISION_BLOCK = 1
COLLISION_WATER = 2
COLLISION_ENTITY = 3
COLLISION_PLAYER = 4


class PhysicsEngine:
    def __init__(self):
        self.space = pymunk.Space()
        self.space.gravity = (0, 0)

        self.bodies = {}
        self.shapes = {}
        self.shape_to_entity = {}

        self.collision_flags = {}

    def update(self, dt=1.0 / 60.0):
        self.space.step(dt)

    def add_static_block(self, x, y, width, height, name=None):
        body = self.space.static_body
        shape = pymunk.Poly.create_box(body, (width, height))
        shape.elasticity = 0.0
        shape.friction = 0.5
        shape.collision_type = COLLISION_BLOCK

        pos = (x + width / 2, y + height / 2)
        shape.body.position = pos

        if name:
            self.shapes[name] = shape

        return shape

    def add_entity_body(
            self, x, y, width, height, name=None, collision_type=COLLISION_ENTITY
    ):
        body = pymunk.Body(body_type=pymunk.Body.KINEMATIC)
        body.position = (x + width / 2, y + height / 2)

        shape = pymunk.Poly.create_box(body, (width, height))
        shape.elasticity = 0.0
        shape.friction = 0.0
        shape.collision_type = collision_type

        self.space.add(body, shape)

        if name:
            self.bodies[name] = body
            self.shapes[name] = shape
            self.shape_to_entity[shape] = name

        return body, shape

    def add_dynamic_body(self, x, y, width, height, mass=1.0, name=None):
        moment = pymunk.moment_for_box(mass, (width, height))
        body = pymunk.Body(mass, moment)
        body.position = (x + width / 2, y + height / 2)

        shape = pymunk.Poly.create_box(body, (width, height))
        shape.elasticity = 0.3
        shape.friction = 0.5
        shape.collision_type = COLLISION_ENTITY

        self.space.add(body, shape)

        if name:
            self.bodies[name] = body

        return body, shape

    def add_kinematic_body(self, x, y, width, height, name=None):
        body = pymunk.Body(body_type=pymunk.Body.KINEMATIC)
        body.position = (x + width / 2, y + height / 2)

        shape = pymunk.Poly.create_box(body, (width, height))
        shape.elasticity = 0.0
        shape.friction = 0.5
        shape.collision_type = COLLISION_BLOCK

        self.space.add(body, shape)

        if name:
            self.bodies[name] = body

        return body, shape

    def apply_force(self, name, force):
        if name in self.bodies:
            self.bodies[name].apply_force_at_local_point(force)

    def apply_impulse(self, name, impulse):
        if name in self.bodies:
            self.bodies[name].apply_impulse_at_local_point(impulse)

    def set_velocity(self, name, velocity):
        if name in self.bodies:
            self.bodies[name].velocity = velocity

    def get_velocity(self, name):
        if name in self.bodies:
            return self.bodies[name].velocity
        return (0, 0)

    def get_position(self, name):
        if name in self.bodies:
            return self.bodies[name].position
        return (0, 0)

    def set_position(self, name, position):
        if name in self.bodies:
            self.bodies[name].position = position

    def remove_body(self, name):
        if name in self.bodies:
            body = self.bodies[name]
            for shape in body.shapes:
                self.space.remove(shape)
                self.shape_to_entity.pop(shape, None)
            self.space.remove(body)
            del self.bodies[name]
            self.shapes.pop(name, None)

    def remove_shape(self, name):
        if name in self.shapes:
            shape = self.shapes[name]
            self.space.remove(shape)
            self.shape_to_entity.pop(shape, None)
            del self.shapes[name]

    def create_collision_handler(
            self,
            type_a,
            type_b,
            begin_handler=None,
            pre_solve_handler=None,
            post_solve_handler=None,
            separate_handler=None,
    ):
        self.space.on_collision(
            type_a,
            type_b,
            begin=begin_handler,
            pre_solve=pre_solve_handler,
            post_solve=post_solve_handler,
            separate=separate_handler,
        )

    def setup_entity_block_handler(self):
        def pre_solve(arbiter, space, data):
            shape_a = arbiter.shapes[0]
            shape_b = arbiter.shapes[1]

            entity_name = self.shape_to_entity.get(shape_a) or self.shape_to_entity.get(
                shape_b
            )
            if entity_name:
                self.collision_flags[entity_name] = True
            return False

        self.create_collision_handler(
            COLLISION_PLAYER, COLLISION_BLOCK, pre_solve_handler=pre_solve
        )
        self.create_collision_handler(
            COLLISION_ENTITY, COLLISION_BLOCK, pre_solve_handler=pre_solve
        )

    def get_objects_at_point(self, x, y):
        point_query = self.space.point_query_nearest((x, y), 0, pymunk.ShapeFilter())
        if point_query:
            return point_query.shape
        return None

    def get_objects_in_rect(self, x, y, width, height):
        rect = pymunk.BB(x, y, x + width, y + height)
        return self.space.shape_query(rect)

    def clear_collision_flags(self):
        self.collision_flags.clear()


class PhysicsEntity:
    def __init__(self, physics, x, y, width, height, mass=1.0, name=None):
        self.physics = physics
        self.name = name
        self.width = width
        self.height = height

        self.body, self.shape = physics.add_dynamic_body(
            x, y, width, height, mass, name
        )

    def get_position(self):
        pos = self.body.position
        return pos.x - self.width / 2, pos.y - self.height / 2

    def set_position(self, x, y):
        self.body.position = (x + self.width / 2, y + self.height / 2)

    def get_velocity(self):
        return self.body.velocity

    def set_velocity(self, vx, vy):
        self.body.velocity = (vx, vy)

    def apply_impulse(self, impulse):
        self.body.apply_impulse_at_local_point(impulse)

    def apply_force(self, force):
        self.body.apply_force_at_local_point(force)

    def destroy(self):
        if self.name and self.name in self.physics.bodies:
            self.physics.remove_body(self.name)


def create_physics_world():
    return PhysicsEngine()
