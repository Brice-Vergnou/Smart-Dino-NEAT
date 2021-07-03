############## IMPORT #################

import pygame
import neat
import os
import sys
import math
from random import randint
from Dinosaur import Dinosaur
from Cloud import Cloud
from Background import Background
from Cactus import Cactus
from Bird import Bird

############ INIT ###########

pygame.init()

################### CONSTANTS ################################

HEIGHT = 720
WIDTH = 1280  # 16:9 format
BACKGROUND = (247, 247, 247)
SCREEN = pygame.display.set_mode((WIDTH, HEIGHT))
FONT = pygame.font.Font("font/visitor.ttf", 30)


############ FUNCTIONS     ##############################


def update_obstacle(type_of_obstacle, obstacle):
    obstacle.update(speed)
    if not type_of_obstacle:
        obstacle.animate()
    obstacle.draw(SCREEN)


def create_obstacle(type_of_obstacle, obstacle):
    if obstacle.X <= randint(100, 340):  # When the bird is near the border , but at a random place , another appears

        list_old_types.append(type_of_obstacle)
        list_types.remove(type_of_obstacle)

        type_of_obstacle = randint(0, 1)

        list_old_obstacles.append(obstacle)
        list_obstacles.remove(obstacle)

        if type_of_obstacle:
            list_obstacles.append(Cactus())
        else:
            list_obstacles.append(Bird())
        list_types.append(type_of_obstacle)
        for g in genomes:
            g.fitness += 5


def statistics():
    text_1 = FONT.render(f'Dinosaurs Alive:  {str(len(dinos))}', True, (0, 0, 0))
    text_2 = FONT.render(f'Generation:  {dinosaurs.generation + 1}', True, (0, 0, 0))
    text_3 = FONT.render(f'Max score:  {max_score}', True, (0, 0, 0))

    SCREEN.blit(text_1, (50, 550))
    SCREEN.blit(text_2, (50, 600))
    SCREEN.blit(text_3, (50, 650))


############ MAIN FUNCTION ###############################


def eval(ge, conf):
    ######  INIT GAME  ###########
    global speed, SCREEN, list_obstacles, list_types, list_old_types, list_old_obstacles, genomes, neural_net, dinos , max_score
    RUNNING = True
    points = 0
    type_of_obstacle = randint(0, 1)  # 0 = Bird , 1 = Cactus
    CLOCK = pygame.time.Clock()
    cloud = Cloud()
    bg = Background()
    pygame.display.set_caption("Smart Dino")
    pygame.display.flip()
    speed = 20

    ##################### CREATE LISTS ########################
    list_types = []
    list_types.append(type_of_obstacle)
    list_obstacles = []
    list_old_obstacles = []
    list_old_types = []
    genomes = []
    neural_net = []
    dinos = []

    # Add dinos
    for i, genome_tuple in enumerate(ge):
        genome = genome_tuple[1]
        dinos.append(Dinosaur())
        genomes.append(genome)
        neural_net.append(neat.nn.FeedForwardNetwork.create(genome, conf))
        genome.fitness = 0

    # Add obstacle
    if type_of_obstacle:
        list_obstacles.append(Cactus())
    else:
        list_obstacles.append(Bird())

    while RUNNING:
        if len(dinos) == 0:
            if points > max_score:
                max_score = math.floor(points)
            break
        for event in pygame.event.get():  # This loops allows the player to quit
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

        input = pygame.key.get_pressed()  # Takes inputs
        SCREEN.fill(BACKGROUND)  # We place it here to overwrite the old dino image

        points += 0.3  # Update score
        score_text = FONT.render("Points : " + str(math.floor(points)), True,
                                 (0, 0, 0))  # The second argument is antialiasing
        SCREEN.blit(score_text, (1000, 50))
        if points % 2 == 0:  # And also speed when score increases
            speed += 0.1

        for dino in dinos:
            dino.update(input)
            dino.draw_image(SCREEN, list_obstacles)

        # To update the obstacle and maybe change it
        for i in range(len(list_obstacles)):
            update_obstacle(list_types[i], list_obstacles[i])
            create_obstacle(list_types[i], list_obstacles[i])
            for j, dino in enumerate(dinos):
                if dino.hitbox.colliderect(list_obstacles[i].hitbox):
                    genomes[j].fitness -= 10  # If collision , decrease the fitness because it's bad and remove it
                    dinos.pop(j)
                    genomes.pop(j)
                    neural_net.pop(j)
                else:
                    genomes[j].fitness += 0.5

        # Just update the old obstacles in case they are still on the screen
        for i in range(len(list_old_obstacles)):
            update_obstacle(list_old_types[i], list_old_obstacles[i])
            for j, dino in enumerate(dinos):
                if dino.hitbox.colliderect(list_old_obstacles[i].hitbox):
                    genomes[j].fitness -= 10  # If collision , decrease the fitness because it's bad and remove it
                    dinos.pop(j)
                    genomes.pop(j)
                    neural_net.pop(j)
                else:
                    genomes[j].fitness += 0.5

        cloud.update(speed)
        cloud.draw(SCREEN)
        if cloud.X <= -100:  # When the cloud is gone , another appears
            cloud = Cloud()

        for i, dino in enumerate(dinos):
            all_obstacles = list_obstacles + list_old_obstacles
            all_types = list_types + list_old_types
            for j, obstacle in enumerate(all_obstacles):
                """ The inputs are :
                        - The y position of the dino
                        - The distance between the dino and the obstacle
                        - The y position of the obstacle
                        - The speed
                        - The width and the height of the obstacle
                        - Distance between the bottom of the dino's hitbox height and the obstacle's one
                """
                output = neural_net[i].activate((dino.hitbox.y,
                                                 obstacle.hitbox.y,
                                                 abs(obstacle.hitbox.x - dino.hitbox.x),
                                                 speed,
                                                 obstacle.image.get_height(),
                                                 obstacle.image.get_width(),
                                                 abs(obstacle.hitbox.midbottom[1] - dino.hitbox.midbottom[1])))

                if output[0] > 0.5 and dino.hitbox.y == dino.Y:
                    dino.is_jumping = True
                    dino.is_running = False
                    dino.is_ducking = False
                if output[1] > 0.5 and not dino.is_jumping:
                    dino.is_ducking = True
                    dino.is_jumping = False
                    dino.is_running = False

        bg.update(speed)
        bg.draw(SCREEN)

        statistics()
        CLOCK.tick(30)  # Refreshing
        pygame.display.update()


############### NEAT CONFIG ###########################

def run(config_txt):  # Setup neat
    global dinosaurs
    config = neat.config.Config(
        neat.DefaultGenome,
        neat.DefaultReproduction,
        neat.DefaultSpeciesSet,
        neat.DefaultStagnation,
        config_txt
    )

    dinosaurs = neat.Population(config)
    dinosaurs.run(eval, 50)


if __name__ == '__main__':
    max_score = 0
    config = os.path.join(os.getcwd(), 'conf.txt')
    run(config)
