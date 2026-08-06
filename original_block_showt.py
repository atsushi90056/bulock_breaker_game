import sys
import random
import pygame

# --- 1. 基本設定 ---
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
FPS = 60

# カラー定義 (RGB)
BLACK = (10, 10, 15)
WHITE = (255, 255, 255)
GRAY = (50, 50, 60)
RED = (239, 83, 80)
ORANGE = (255, 167, 38)
YELLOW = (255, 238, 88)
GREEN = (102, 187, 106)
CYAN = (38, 198, 218)
PURPLE = (171, 71, 188)

BLOCK_COLORS = [RED, ORANGE, YELLOW, GREEN, CYAN]

# アイテム設定
ITEM_TYPES = {
    "WIDE": {"color": CYAN, "label": "W"},
    "SLOW": {"color": GREEN, "label": "S"},
    "PENETRATE": {"color": RED, "label": "P"},
    "MULTI": {"color": PURPLE, "label": "M"}
}


class Ball:
    def __init__(self, x, y, dx, dy):
        self.x = x
        self.y = y
        self.dx = dx
        self.dy = dy
        self.radius = 8

    def update(self, speed_factor):
        self.x += self.dx * speed_factor
        self.y += self.dy * speed_factor

    def get_rect(self):
        return pygame.Rect(
            self.x - self.radius,
            self.y - self.radius,
            self.radius * 2,
            self.radius * 2
        )


class Item:
    def __init__(self, x, y, item_type):
        self.rect = pygame.Rect(x, y, 24, 24)
        self.type = item_type
        self.speed = 3

    def update(self):
        self.rect.y += self.speed


class BlockBreaker:
    def __init__(self):
        self.base_paddle_width = 120
        self.paddle_height = 15
        self.paddle_y = SCREEN_HEIGHT - 50
        self.paddle_speed = 8

        self.cols = 10
        self.rows = 5
        self.block_width = 70
        self.block_height = 20
        self.block_padding = 8
        self.block_offset_top = 60
        self.block_offset_left = (
            SCREEN_WIDTH - (self.cols * (self.block_width + self.block_padding))
        ) // 2

        # ゲーム状態の初期化
        self.reset_game()

    def reset_game(self):
        """ゲーム全体を初期状態にリセット"""
        self.paddle_width = self.base_paddle_width
        self.paddle_x = (SCREEN_WIDTH - self.paddle_width) // 2

        self.reset_balls()

        self.wide_timer = 0
        self.slow_timer = 0
        self.penetrate_timer = 0

        self.items = []
        self.blocks = []
        self.init_blocks()

        self.score = 0
        self.game_over = False
        self.game_clear = False

    def reset_balls(self):
        init_ball = Ball(
            SCREEN_WIDTH // 2,
            self.paddle_y - 10,
            5,
            -5
        )
        self.balls = [init_ball]

    def init_blocks(self):
        for r in range(self.rows):
            for c in range(self.cols):
                bx = self.block_offset_left + c * (
                    self.block_width + self.block_padding
                )
                by = self.block_offset_top + r * (
                    self.block_height + self.block_padding
                )
                color = BLOCK_COLORS[r % len(BLOCK_COLORS)]
                rect = pygame.Rect(bx, by, self.block_width, self.block_height)
                self.blocks.append({"rect": rect, "color": color})

    def spawn_multi_balls(self):
        new_balls = []
        for b in self.balls:
            b1 = Ball(b.x, b.y, -abs(b.dx) - 1, -abs(b.dy))
            b2 = Ball(b.x, b.y, abs(b.dx) + 1, -abs(b.dy))
            new_balls.extend([b1, b2])
        self.balls.extend(new_balls)

    def apply_item(self, item_type):
        if item_type == "WIDE":
            self.wide_timer = 600
            self.paddle_width = 180
        elif item_type == "SLOW":
            self.slow_timer = 600
        elif item_type == "PENETRATE":
            self.penetrate_timer = 400
        elif item_type == "MULTI":
            self.spawn_multi_balls()

    def update_timers(self):
        if self.wide_timer > 0:
            self.wide_timer -= 1
            if self.wide_timer == 0:
                self.paddle_width = self.base_paddle_width

        if self.slow_timer > 0:
            self.slow_timer -= 1

        if self.penetrate_timer > 0:
            self.penetrate_timer -= 1

    def update(self, keys):
        if self.game_over or self.game_clear:
            return

        self.update_timers()

        # パドル移動
        if keys[pygame.K_LEFT] and self.paddle_x > 0:
            self.paddle_x -= self.paddle_speed
        if keys[pygame.K_RIGHT] and self.paddle_x < SCREEN_WIDTH - self.paddle_width:
            self.paddle_x += self.paddle_speed

        paddle_rect = pygame.Rect(
            self.paddle_x, self.paddle_y, self.paddle_width, self.paddle_height
        )

        speed_factor = 0.5 if self.slow_timer > 0 else 1.0

        for ball in self.balls[:]:
            ball.update(speed_factor)
            ball_rect = ball.get_rect()

            if ball.x - ball.radius <= 0 or ball.x + ball.radius >= SCREEN_WIDTH:
                ball.dx *= -1
            if ball.y - ball.radius <= 0:
                ball.dy *= -1

            if ball.y - ball.radius >= SCREEN_HEIGHT:
                self.balls.remove(ball)
                continue

            if ball_rect.colliderect(paddle_rect) and ball.dy > 0:
                ball.dy *= -1
                paddle_center = self.paddle_x + self.paddle_width / 2
                hit_pos = (ball.x - paddle_center) / (self.paddle_width / 2)
                ball.dx = hit_pos * 7

            for block in self.blocks[:]:
                if ball_rect.colliderect(block["rect"]):
                    self.blocks.remove(block)
                    self.score += 10

                    if self.penetrate_timer == 0:
                        ball.dy *= -1

                    if random.random() < 0.35:
                        item_type = random.choice(list(ITEM_TYPES.keys()))
                        self.items.append(
                            Item(
                                block["rect"].centerx,
                                block["rect"].centery,
                                item_type,
                            )
                        )

                    if self.penetrate_timer == 0:
                        break

        if not self.balls:
            self.game_over = True

        for item in self.items[:]:
            item.update()
            if item.rect.colliderect(paddle_rect):
                self.apply_item(item.type)
                self.items.remove(item)
            elif item.rect.y > SCREEN_HEIGHT:
                self.items.remove(item)

        if not self.blocks:
            self.game_clear = True


def main():
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("Block Breaker - Retry Enabled")
    clock = pygame.time.Clock()

    game = BlockBreaker()

    font_large = pygame.font.SysFont("arial", 40, bold=True)
    font_small = pygame.font.SysFont("arial", 20, bold=True)

    while True:
        clock.tick(FPS)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            # --- リトライ（'R'キー）の判定 ---
            if event.type == pygame.KEYDOWN:
                if (game.game_over or game.game_clear) and event.key == pygame.K_r:
                    game.reset_game()

        keys = pygame.key.get_pressed()
        game.update(keys)

        # --- 描画処理 ---
        screen.fill(BLACK)

        # 1. ブロック描画
        for block in game.blocks:
            pygame.draw.rect(screen, block["color"], block["rect"], border_radius=3)

        # 2. パドル描画
        paddle_color = CYAN if game.wide_timer > 0 else WHITE
        pygame.draw.rect(
            screen,
            paddle_color,
            (
                game.paddle_x,
                game.paddle_y,
                game.paddle_width,
                game.paddle_height,
            ),
            border_radius=5,
        )

        # 3. ボール描画
        ball_color = RED if game.penetrate_timer > 0 else CYAN
        for ball in game.balls:
            pygame.draw.circle(
                screen,
                ball_color,
                (int(ball.x), int(ball.y)),
                ball.radius,
            )

        # 4. アイテム描画
        for item in game.items:
            info = ITEM_TYPES[item.type]
            pygame.draw.rect(screen, info["color"], item.rect, border_radius=4)
            label = font_small.render(info["label"], True, BLACK)
            screen.blit(label, (item.rect.x + 6, item.rect.y + 2))

        # 5. UI描画
        score_surface = font_small.render(f"Score: {game.score}", True, WHITE)
        balls_surface = font_small.render(f"Balls: {len(game.balls)}", True, PURPLE)
        screen.blit(score_surface, (20, 15))
        screen.blit(balls_surface, (140, 15))

        status_text = ""
        if game.wide_timer > 0:
            status_text += "[WIDE] "
        if game.slow_timer > 0:
            status_text += "[SLOW] "
        if game.penetrate_timer > 0:
            status_text += "[PENETRATE] "

        if status_text:
            status_surface = font_small.render(
                f"EFFECTS: {status_text}", True, YELLOW
            )
            screen.blit(status_surface, (260, 15))

        # 6. ゲームオーバー / クリア ＆ リトライ案内表示
        if game.game_over:
            msg = font_large.render("GAME OVER", True, RED)
            rect = msg.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 20))
            screen.blit(msg, rect)

            retry_msg = font_small.render("PRESS 'R' TO RESTART", True, WHITE)
            retry_rect = retry_msg.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 30))
            screen.blit(retry_msg, retry_rect)

        elif game.game_clear:
            msg = font_large.render("GAME CLEAR!", True, GREEN)
            rect = msg.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 20))
            screen.blit(msg, rect)

            retry_msg = font_small.render("PRESS 'R' TO RESTART", True, WHITE)
            retry_rect = retry_msg.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 30))
            screen.blit(retry_msg, retry_rect)

        pygame.display.flip()


if __name__ == "__main__":
    main()