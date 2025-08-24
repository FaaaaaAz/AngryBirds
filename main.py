import math
import arcade
import pymunk
from pathlib import Path

from game_object import Bird, BlueBird, YellowBird, Pig, Column, Beam
from game_logic import Point2D, get_distance, get_angle_radians, get_impulse_vector

SCREEN_WIDTH = 1200
SCREEN_HEIGHT = 650
SCREEN_TITLE = "Angry Birds"

ASSETS_PATH = Path(__file__).parent / "assets" / "img"


SLING_X = 200
SLING_Y = 200
SLING_ACTIVATE_RADIUS = 80

COLLISION_KILL_THRESHOLD = 1200


class AngryBirds(arcade.Window):
    def __init__(self):
        super().__init__(SCREEN_WIDTH, SCREEN_HEIGHT, SCREEN_TITLE)

        bg_path = ASSETS_PATH / "background3.png"
        if not bg_path.exists():
            raise FileNotFoundError(f"Falta el asset: {bg_path}")

        bg_sprite = arcade.Sprite(str(bg_path), scale=1.0)
        if bg_sprite.width > 0:
            bg_sprite.scale = SCREEN_WIDTH / bg_sprite.width
        bg_sprite.center_x = SCREEN_WIDTH // 2
        bg_sprite.center_y = SCREEN_HEIGHT // 2
        self.bg_list = arcade.SpriteList()
        self.bg_list.append(bg_sprite)
        sling_path = ASSETS_PATH / "sling-3.png"
        if sling_path.exists():
            self.slingshot_sprite = arcade.Sprite(str(sling_path), scale=0.4)
            self.slingshot_sprite.center_x = SLING_X
            self.slingshot_sprite.center_y = SLING_Y
            self.sling_list = arcade.SpriteList()
            self.sling_list.append(self.slingshot_sprite)
        else:
            self.slingshot_sprite = None
            self.sling_list = arcade.SpriteList()

        self.launch_icon_path = ASSETS_PATH / "click_left.png"
        self.power_icon_path = ASSETS_PATH / "click_right.png"
        self.red_tex_path = str(ASSETS_PATH / "red-bird3.png")
        self.blue_tex_path = str(ASSETS_PATH / "blue.png")
        self.yellow_tex_path = str(ASSETS_PATH / "chuck.png")  # puede llamarse chuck.png

        self.space = pymunk.Space()
        self.space.gravity = (0, -900)
        handler = self.space.add_default_collision_handler()
        handler.post_solve = self.collision_handler
        self._collision_handler = handler

        floor_body = pymunk.Body(body_type=pymunk.Body.STATIC)
        floor_shape = pymunk.Segment(floor_body, (0, 15), (SCREEN_WIDTH, 15), 0.0)
        floor_shape.friction = 10.0
        self.space.add(floor_body, floor_shape)

        self.world = arcade.SpriteList() 
        self.birds = arcade.SpriteList() 
        self.ui_list = arcade.SpriteList() 
        self._add_basic_scene()
        self.start_point = Point2D()
        self.end_point = Point2D()
        self.draw_line = False
        self.draw_slingshot = False
        self.current_bird_kind = "Red"
        self.current_bird_image = self.red_tex_path
        self.won = False
        self._prepare_ui_sprites()

    def _prepare_ui_sprites(self):
        icon_w = 45
        icon_h = 45

        x_position = 10
        y_position_launch = SCREEN_HEIGHT - 60
        if Path(self.launch_icon_path).exists():
            ico = arcade.Sprite(self.launch_icon_path, scale=1.0)
            if ico.width > 0:
                ico.scale = icon_w / ico.width
            ico.center_x = x_position + icon_w / 2
            ico.center_y = y_position_launch - icon_h / 2
            self.ui_list.append(ico)

        y_position_power = y_position_launch - icon_h - 10
        if Path(self.power_icon_path).exists():
            ico2 = arcade.Sprite(self.power_icon_path, scale=1.0)
            if ico2.width > 0:
                ico2.scale = icon_w / ico2.width
            ico2.center_x = x_position + icon_w / 2
            ico2.center_y = y_position_power - icon_h / 2
            self.ui_list.append(ico2)

        bird_icons = [
            (self.red_tex_path, "Z", "Red"),
            (self.blue_tex_path, "X", "Blue"),
            (self.yellow_tex_path, "C", "Yellow"),
        ]
        x_pos_icons = SCREEN_WIDTH - (icon_w + 450)
        for index, (icon_path, key, name) in enumerate(bird_icons):
            if Path(icon_path).exists():
                icon_sprite = arcade.Sprite(icon_path, scale=1.0)
                if icon_sprite.width > 0:
                    icon_sprite.scale = icon_w / icon_sprite.width
                y_pos = SCREEN_HEIGHT - (60 + index * (icon_h + 20))
                icon_sprite.center_x = x_pos_icons + icon_w / 2
                icon_sprite.center_y = y_pos - icon_h / 2
                icon_sprite._meta = {"key": key, "name": name}
                self.ui_list.append(icon_sprite)

    def _add_basic_scene(self):
        self.world.append(Column(SCREEN_WIDTH // 2 + 40, 150, self.space))
        self.world.append(Column(SCREEN_WIDTH // 2 + 117, 150, self.space))
        self.world.append(Beam(SCREEN_WIDTH // 2 + 79, 200, self.space))

        self.world.append(Column(SCREEN_WIDTH // 2, 50, self.space))
        self.world.append(Column(SCREEN_WIDTH // 2 + 77, 50, self.space))
        self.world.append(Column(SCREEN_WIDTH // 2 + 154, 50, self.space))
        self.world.append(Beam(SCREEN_WIDTH // 2 + 35, 100, self.space))
        self.world.append(Beam(SCREEN_WIDTH // 2 + 120, 100, self.space))

        self.world.append(Pig(SCREEN_WIDTH // 2 + 50, 50, self.space))
        self.world.append(Pig(SCREEN_WIDTH // 2 + 125, 50, self.space))
        self.world.append(Pig(SCREEN_WIDTH // 2 + 90, 150, self.space))

    def on_key_press(self, key, modifiers):
        if key == arcade.key.Z:
            self.current_bird_kind = "Red"
            self.current_bird_image = self.red_tex_path
        elif key == arcade.key.X:
            self.current_bird_kind = "Blue"
            self.current_bird_image = self.blue_tex_path
        elif key == arcade.key.C:
            self.current_bird_kind = "Yellow"
            self.current_bird_image = self.yellow_tex_path

    def on_mouse_press(self, x, y, button, modifiers):
        if button == arcade.MOUSE_BUTTON_LEFT:
            dist_to_sling = math.hypot(x - SLING_X, y - SLING_Y)
            if dist_to_sling <= SLING_ACTIVATE_RADIUS:
                self.start_point = Point2D(x, y)
                self.end_point = Point2D(x, y)
                self.draw_line = True
                self.draw_slingshot = True
            else:
                pass

        elif button == arcade.MOUSE_BUTTON_RIGHT:
            for b in list(self.birds):
                try:
                    if isinstance(b, (BlueBird, YellowBird)) and not getattr(b, "_power_used", False):
                        if getattr(b, "body", None) and b.body.velocity.length > 1:
                            b.on_click()
                except Exception:
                    pass

    def on_mouse_drag(self, x, y, dx, dy, buttons, modifiers):
        if buttons == arcade.MOUSE_BUTTON_LEFT:
            temp = Point2D(x, y)
            dist = get_distance(self.start_point, temp)
            if dist > 100:
                angle = get_angle_radians(self.start_point, temp)
                x = self.start_point.x - 100 * math.cos(angle)
                y = self.start_point.y - 100 * math.sin(angle)
            self.end_point = Point2D(x, y)

    def on_mouse_release(self, x, y, button, modifiers):
        if button != arcade.MOUSE_BUTTON_LEFT:
            return

        self.draw_line = False
        self.draw_slingshot = False
        temp = Point2D(x, y)
        dist = get_distance(self.start_point, temp)
        if dist > 100:
            angle = get_angle_radians(self.start_point, temp)
            x = self.start_point.x - 100 * math.cos(angle)
            y = self.start_point.y - 100 * math.sin(angle)
        self.end_point = Point2D(x, y)

        iv = get_impulse_vector(self.start_point, self.end_point)
        scale_map = {"Red": 0.80, "Blue": 0.11, "Yellow": 0.11}
        base_scale = scale_map.get(self.current_bird_kind, 0.14)

        if self.current_bird_kind == "Yellow":
            bird = YellowBird(self.current_bird_image, iv, self.end_point.x, self.end_point.y, self.space, sprite_scale=base_scale)
        elif self.current_bird_kind == "Blue":
            bird = BlueBird(self.current_bird_image, iv, self.end_point.x, self.end_point.y, self.space,
                            sprites_list=self.birds, birds_list=self.birds, sprite_scale=base_scale)
        else:
            bird = Bird(self.current_bird_image, iv, self.end_point.x, self.end_point.y, self.space, sprite_scale=base_scale)

        self.birds.append(bird)

    def on_update(self, delta_time: float):
        self.space.step(1 / 60.0)
        self.world.update()
        self.birds.update()

        for b in list(self.birds):
            if b.center_y < -150 or b.center_x > SCREEN_WIDTH + 300:
                b.remove_from_sprite_lists()
                try:
                    self.space.remove(b.shape, b.body)
                except Exception:
                    pass

        if not self.won:
            pig_count = sum(1 for obj in self.world if isinstance(obj, Pig))
            if pig_count == 0:
                self.won = True

    def collision_handler(self, arbiter, space, data):
        try:
            impulse_norm = arbiter.total_impulse.length
        except Exception:
            return True

        if impulse_norm < 100:
            return True

        if impulse_norm > COLLISION_KILL_THRESHOLD:
            for obj in list(self.world):
                try:
                    if hasattr(obj, "shape") and obj.shape in arbiter.shapes:
                        obj.remove_from_sprite_lists()
                        try:
                            self.space.remove(obj.shape, obj.body)
                        except Exception:
                            pass
                except Exception:
                    pass

            for b in list(self.birds):
                try:
                    if hasattr(b, "shape") and b.shape in arbiter.shapes:
                        b.remove_from_sprite_lists()
                        try:
                            self.space.remove(b.shape, b.body)
                        except Exception:
                            pass
                except Exception:
                    pass

        return True

    def on_draw(self):
        self.clear()

        try:
            self.bg_list.draw()
        except Exception:
            pass

        
        if self.slingshot_sprite:
            self.sling_list.draw()

        arcade.draw_circle_outline(SLING_X, SLING_Y, SLING_ACTIVATE_RADIUS, (0, 0, 0), 2)
        text_y = SLING_Y + SLING_ACTIVATE_RADIUS + 40
        arcade.draw_text(
            "Click derecho para activar poder.",
            SLING_X + SLING_ACTIVATE_RADIUS + 10,
            text_y,
            arcade.color.BLACK,
            14
        )

        self.world.draw()
        self.birds.draw()

        if self.draw_line:
            arcade.draw_line(self.start_point.x, self.start_point.y,
                             self.end_point.x, self.end_point.y,
                             arcade.color.BLACK, 3)

            if self.slingshot_sprite:
                self.slingshot_sprite.center_x = self.start_point.x
                self.slingshot_sprite.center_y = self.start_point.y
                try:
                    self.slingshot_sprite.draw()
                except Exception:
                    pass

        
        try:
            self.ui_list.draw()
        except Exception:
            pass
    
        icon_w = 45
        x_pos_icons = SCREEN_WIDTH - (icon_w + 450)
        for idx, meta in enumerate([("Z", "Red"), ("X", "Blue"), ("C", "Yellow")]):
            key, name = meta
            y_pos = SCREEN_HEIGHT - (60 + idx * (icon_w + 20))
            arcade.draw_text(f"Tecla: {key}", x_pos_icons + icon_w + 10, y_pos - icon_w / 2 + 7, arcade.color.BLACK, 14)
            arcade.draw_text(f"Pájaro: {name}", x_pos_icons + icon_w + 10, y_pos - icon_w / 2 - 15, arcade.color.BLACK, 14)

        if self.won:
            cx = SCREEN_WIDTH // 2
            cy = SCREEN_HEIGHT // 2
            w = 500
            h = 120
            left = cx - w // 2
            right = cx + w // 2
            top = cy + h // 2
            bottom = cy - h // 2
            arcade.draw_lrtb_rectangle_filled(left, right, top, bottom, (255, 255, 255, 230))
            arcade.draw_text("¡GANASTE!", cx, cy + 10, arcade.color.DARK_GREEN, 36, anchor_x="center")
            arcade.draw_text("Felicidades: todos los cerdos fueron eliminados.", cx, cy - 20, arcade.color.BLACK, 16, anchor_x="center")


def main():
    game = AngryBirds()
    arcade.run()


if __name__ == "__main__":
    main()
