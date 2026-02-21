import pygame
import sqlite3
import random
import sys

SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
FPS = 60

WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (200, 50, 50)
GREEN = (50, 200, 50)
BLUE = (50, 50, 200)
YELLOW = (255, 223, 0)

# параметры игры
PLAYER_SPEED = 8
BULLET_SPEED = 7
ENEMY_SPEED = 3
WIN_SCORE = 20  

class DatabaseHandler:
    def __init__(self, db_name="game_scores.db"):
        self.connection = sqlite3.connect(db_name)
        self.cursor = self.connection.cursor()
        self.createTable()

    def createTable(self):
        """Создает таблицу, если она не существует"""
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT,
                score INTEGER
            )
        """)
        self.connection.commit()

    def addScore(self, name, score):
        self.cursor.execute("INSERT INTO records (name, score) VALUES (?, ?)", (name, score))
        self.connection.commit()

    def getTop5(self):
        self.cursor.execute("SELECT name, score FROM records ORDER BY score DESC LIMIT 5")
        return self.cursor.fetchall()

    def close(self):
        self.connection.close()

class Player(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        
        self.image = pygame.Surface((50, 40))
        self.image.fill(GREEN) 
        self.rect = self.image.get_rect()
        self.rect.centerx = SCREEN_WIDTH // 2
        self.rect.bottom = SCREEN_HEIGHT - 10
        self.speed_x = 0

    def update(self):
        
        self.speed_x = 0
        keys = pygame.key.get_pressed()
        if keys[pygame.K_LEFT]:
            self.speed_x = -PLAYER_SPEED
        if keys[pygame.K_RIGHT]:
            self.speed_x = PLAYER_SPEED
        
        self.rect.x += self.speed_x

        if self.rect.right > SCREEN_WIDTH:
            self.rect.right = SCREEN_WIDTH
        if self.rect.left < 0:
            self.rect.left = 0

    def shoot(self):
        bullet = Bullet(self.rect.centerx, self.rect.top)
        return bullet

class Enemy(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        self.image = pygame.Surface((40, 40))
        self.image.fill(RED)
        self.rect = self.image.get_rect()
        self.rect.x = random.randrange(0, SCREEN_WIDTH - self.rect.width)
        self.rect.y = random.randrange(-100, -40)
        self.speed_y = random.randrange(2, 5)

    def update(self):
        self.rect.y += self.speed_y

        if self.rect.top > SCREEN_HEIGHT + 10:
            self.kill() 

class Bullet(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        self.image = pygame.Surface((10, 20))
        self.image.fill(YELLOW)
        self.rect = self.image.get_rect()
        self.rect.bottom = y
        self.rect.centerx = x
        self.speed_y = -BULLET_SPEED

    def update(self):
        self.rect.y += self.speed_y
        if self.rect.bottom < 0:
            self.kill()


class Game:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Cannon Defender")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.Font(None, 36)
        self.big_font = pygame.font.Font(None, 72)
        
        self.db = DatabaseHandler()
        self.player_name = ""
        self.score = 0
        self.game_over = False
        self.win = False

    def draw_text(self, text, font, color, x, y, center=False):
        text_obj = font.render(text, True, color)
        text_rect = text_obj.get_rect()
        if center:
            text_rect.center = (x, y)
        else:
            text_rect.topleft = (x, y)
        self.screen.blit(text_obj, text_rect)

    def get_user_name(self):
        input_active = True
        user_text = ''
        
        while input_active:
            self.screen.fill(BLACK)
            self.draw_text("ВВЕДИТЕ ВАШЕ ИМЯ:", self.big_font, WHITE, SCREEN_WIDTH//2, SCREEN_HEIGHT//2 - 50, center=True)
            self.draw_text(user_text, self.big_font, YELLOW, SCREEN_WIDTH//2, SCREEN_HEIGHT//2 + 50, center=True)
            self.draw_text("Нажмите ENTER, чтобы начать", self.font, WHITE, SCREEN_WIDTH//2, SCREEN_HEIGHT - 100, center=True)
            
            pygame.display.flip()

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_RETURN:
                        if len(user_text) > 0:
                            self.player_name = user_text
                            input_active = False
                    elif event.key == pygame.K_BACKSPACE:
                        user_text = user_text[:-1]
                    else:
                        # Ограничим длину имени 10 символами
                        if len(user_text) < 10:
                            user_text += event.unicode

    def show_end_screen(self):
        """Экран завершения (Победа/Поражение + Топ 5)"""
        self.db.addScore(self.player_name, self.score)
        top_records = self.db.getTop5()

        waiting = True
        while waiting:
            self.screen.fill(BLACK)
            
            if self.win:
                self.draw_text("ПОБЕДА!", self.big_font, GREEN, SCREEN_WIDTH//2, 50, center=True)
            else:
                self.draw_text("ИГРА ОКОНЧЕНА", self.big_font, RED, SCREEN_WIDTH//2, 50, center=True)

            self.draw_text(f"Ваш счет: {self.score}", self.font, WHITE, SCREEN_WIDTH//2, 120, center=True)
            
            self.draw_text("ТОП-5 ИГРОКОВ:", self.font, YELLOW, SCREEN_WIDTH//2, 180, center=True)
            
            y_offset = 220
            for idx, (name, score) in enumerate(top_records):
                text = f"{idx + 1}. {name} - {score}"
                self.draw_text(text, self.font, WHITE, SCREEN_WIDTH//2, y_offset, center=True)
                y_offset += 30

            self.draw_text("Нажмите ПРОБЕЛ, чтобы выйти", self.font, WHITE, SCREEN_WIDTH//2, SCREEN_HEIGHT - 50, center=True)
            
            pygame.display.flip()

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    waiting = False
                    pygame.quit()
                    sys.exit()
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_SPACE:
                        waiting = False

    def run(self):
        self.get_user_name()

        # инициализация игровых объектов
        all_sprites = pygame.sprite.Group()
        mobs = pygame.sprite.Group()
        bullets = pygame.sprite.Group()
        
        player = Player()
        all_sprites.add(player)

        ADDENEMY = pygame.USEREVENT + 1
        pygame.time.set_timer(ADDENEMY, 1000) # каждый враг раз в секунду

        running = True
        while running:
            # обработка событий
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == ADDENEMY:
                    # создание врага
                    enemy = Enemy()
                    all_sprites.add(enemy)
                    mobs.add(enemy)
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_SPACE:
                        # стрельба
                        bullet = player.shoot()
                        all_sprites.add(bullet)
                        bullets.add(bullet)

            # обновление
            all_sprites.update()

            # проверка попаданий (пуля и враг)
            hits = pygame.sprite.groupcollide(mobs, bullets, True, True)
            for hit in hits:
                self.score += 1 # подсчет очков

            # условие ПОБЕДЫ
            if self.score >= WIN_SCORE:
                self.win = True
                running = False

            # линия проигрыша - низ экрана - луз
            for mob in mobs:
                if mob.rect.top >= SCREEN_HEIGHT:
                    self.game_over = True
                    running = False

            # отрисовка
            self.screen.fill(BLACK)
            all_sprites.draw(self.screen)
            
            # HUD
            self.draw_text(f"Игрок: {self.player_name}", self.font, WHITE, 10, 10)
            self.draw_text(f"Счет: {self.score} / {WIN_SCORE}", self.font, WHITE, SCREEN_WIDTH - 200, 10)
            self.draw_text("Управление: Стрелки + Пробел", self.font, WHITE, 10, SCREEN_HEIGHT - 30)

            pygame.display.flip()
            self.clock.tick(FPS)

        # конец игры
        self.show_end_screen()
        self.db.close()
        pygame.quit()

if __name__ == "__main__":
    game = Game()
    game.run()