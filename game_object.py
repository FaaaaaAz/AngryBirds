import math
import arcade
import pymunk
from game_logic import ImpulseVector


class Bird(arcade.Sprite):
    def __init__(
        self,
        image_path: str,
        impulse_vector: ImpulseVector,
        x: float,
        y: float,
        space: pymunk.Space,
        mass: float = 5,
        radius: float = 12,
        max_impulse: float = 100,
        power_multiplier: float = 50,
        elasticity: float = 0.8,
        friction: float = 1.0,
        collision_layer: int = 0,
        sprite_scale: float = 0.14,
        **kwargs
    ):
        self._image_path = image_path
        super().__init__(image_path, sprite_scale)

        moment = pymunk.moment_for_circle(mass, 0, radius)
        body = pymunk.Body(mass, moment)
        body.position = (x, y)

        capped = min(max_impulse, max(0.0, impulse_vector.impulse))
        initial_impulse_value = capped * power_multiplier
        impulse_vec = pymunk.Vec2d(initial_impulse_value, 0).rotated(impulse_vector.angle)
        body.apply_impulse_at_local_point(impulse_vec)

        shape = pymunk.Circle(body, radius)
        shape.elasticity = elasticity
        shape.friction = friction
        shape.collision_type = collision_layer

        space.add(body, shape)

        self.body = body
        self.shape = shape
        self._initial_impulse_value = initial_impulse_value
        self._power_used = True 

    def on_click(self):
        pass

    def update(self, delta_time: float = 1 / 60):
        self.center_x = self.shape.body.position.x
        self.center_y = self.shape.body.position.y
        self.radians = self.shape.body.angle


class YellowBird(Bird):

    def __init__(
        self,
        image_path: str,
        impulse_vector: ImpulseVector,
        x: float,
        y: float,
        space: pymunk.Space,
        impulse_multiplier: float = 2.0,
        **kwargs
    ):
        super().__init__(image_path, impulse_vector, x, y, space, **kwargs)
        self.impulse_multiplier = impulse_multiplier
        self._power_used = False

    def on_click(self):
        if self._power_used:
            return
        extra_value = max(0.0, (self.impulse_multiplier - 1.0)) * self._initial_impulse_value
        extra_vec = pymunk.Vec2d(extra_value, 0).rotated(self.body.angle)
        self.body.apply_impulse_at_local_point(extra_vec)
        self._power_used = True


class BlueBird(Bird):
    def __init__(
        self,
        image_path: str,
        impulse_vector: ImpulseVector,
        x: float,
        y: float,
        space: pymunk.Space,
        sprites_list: arcade.SpriteList,
        birds_list: arcade.SpriteList,
        **kwargs
    ):
        super().__init__(image_path, impulse_vector, x, y, space, **kwargs)
        self._power_used = False
        self._sprites_list = sprites_list
        self._birds_list = birds_list

    def on_click(self):
        if self._power_used:
            return
        self._power_used = True

        base_speed = self.body.velocity.length
        if base_speed <= 0:
            return

        base_angle = self.body.angle
        offsets = [math.radians(30), 0.0, -math.radians(30)]

        base_scale = getattr(self, "scale", 0.14)

        for off in offsets:
            angle = base_angle + off
            nb = Bird(
                self._image_path,
                ImpulseVector(0.0, 0.0),
                self.body.position.x,
                self.body.position.y,
                self.shape.space,
                sprite_scale=base_scale,
            )
            nb.body.velocity = pymunk.Vec2d(base_speed, 0).rotated(angle)
            nb.body.angle = angle
            self._sprites_list.append(nb)
            self._birds_list.append(nb)

        try:
            self.remove_from_sprite_lists()
        except Exception:
            pass
        try:
            self.shape.space.remove(self.shape, self.body)
        except Exception:
            pass


class Pig(arcade.Sprite):
    def __init__(
        self,
        x: float,
        y: float,
        space: pymunk.Space,
        mass: float = 2.0,
        elasticity: float = 0.8,
        friction: float = 0.4,
        collision_layer: int = 0,
    ):
        super().__init__("assets/img/pig_failed.png", 0.1)
        moment = pymunk.moment_for_circle(mass, 0, self.width / 2 - 3)
        body = pymunk.Body(mass, moment)
        body.position = (x, y)
        shape = pymunk.Circle(body, self.width / 2 - 3)
        shape.elasticity = elasticity
        shape.friction = friction
        shape.collision_type = collision_layer
        space.add(body, shape)
        self.body = body
        self.shape = shape

    def update(self, delta_time: float = 1 / 60):
        self.center_x = self.shape.body.position.x
        self.center_y = self.shape.body.position.y
        self.radians = self.shape.body.angle


class PassiveObject(arcade.Sprite):
    def __init__(
        self,
        image_path: str,
        x: float,
        y: float,
        space: pymunk.Space,
        mass: float = 2.0,
        elasticity: float = 0.8,
        friction: float = 1.0,
        collision_layer: int = 0,
    ):
        super().__init__(image_path, 1)
        moment = pymunk.moment_for_box(mass, (self.width, self.height))
        body = pymunk.Body(mass, moment)
        body.position = (x, y)
        shape = pymunk.Poly.create_box(body, (self.width, self.height))
        shape.elasticity = elasticity
        shape.friction = friction
        shape.collision_type = collision_layer
        space.add(body, shape)
        self.body = body
        self.shape = shape

    def update(self, delta_time: float = 1 / 60):
        self.center_x = self.shape.body.position.x
        self.center_y = self.shape.body.position.y
        self.radians = self.shape.body.angle


class Column(PassiveObject):
    def __init__(self, x, y, space):
        super().__init__("assets/img/column.png", x, y, space)


class Beam(PassiveObject):
    def __init__(self, x, y, space):
        super().__init__("assets/img/beam.png", x, y, space)


class StaticObject(arcade.Sprite):
    def __init__(
        self,
        image_path: str,
        x: float,
        y: float,
        space: pymunk.Space,
        mass: float = 2.0,
        elasticity: float = 0.8,
        friction: float = 1.0,
        collision_layer: int = 0,
    ):
        super().__init__(image_path, 1)
