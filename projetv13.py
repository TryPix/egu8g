"""
Projet - eGu8g.

Sources:
- https://stackoverflow.com/questions/32449670/tkinter-tclerror-bad-screen-
distance-in-pythons-tkinter-when-trying-to-modi
- https://stackoverflow.com/questions/3408779/how-to-rotate-a-polygon-on-a-
tkinter-canvas
- https://www.c-sharpcorner.com/blogs/basics-for-displaying-image-in-tkinter-
python
"""


import tkinter as tk
from math import cos, sin, sqrt, acos
import time
import itertools
from copy import deepcopy
import random


class VueTower:
    """
    La vue de la classe Tower.

    Attributs:
        - c : canvas Tkinter
        - center : coordonnées du centre de rotation
        - draw_tower(x, y) : dessine la tour à (x, y)
        - borders : [[xmin, ymin], [xmax, ymax]] (pour les collisions)
        - xy : toutes les coordonnées définissant la tour.
    """

    def __init__(self, canvas, center):
        self.center = center
        self.c = canvas
        x, y = self.center
        self._xy2 = [x-10,y-25, x,y-50, x+10,y-25]
        self._xy3 = [x-25,y-10, x-50,y, x-25,y+10]
        self._xy4 = [x-10,y+25, x,y+50, x+10,y+25]
        self._xy5 = [x+25,y-10, x+50,y, x+25,y+10]
        self.borders = [x-25, y-25, x+25, y+25]
        self.xy = [[x-6,y-6],[x-6,y+6],[x+50,y+6],[x+50,y-6]]

    def draw_tower(self, x, y, spawn = False, fill = False):
        """Dessine la tour sur le canvas."""
        self.c.create_polygon(self._xy2, fill = "#7d8cc4", tag =["tower"])
        self.c.create_polygon(self._xy3, fill = "#7d8cc4", tag =["tower"])
        self.c.create_polygon(self._xy4, fill = "#7d8cc4", tag =["tower"])
        self.c.create_polygon(self._xy5, fill = "#7d8cc4", tag =["tower"])
        if not spawn:
            self.c.create_rectangle(self.borders, fill = "black", tag =["tower"])
            self.c.create_rectangle(x-10, y-10, x+10, y+10, fill = "#bee7e8", tag =["tower"])


class ModeleTower:
    """
    Le modèle du Tower. Contient les valeurs stockées initialement, ainsi que
    des procédures simples (trigonométrie et Pythagore).

    Attributs :
        - BULLET_VELOCITY : vitesse des balles
        - c : canvas
        - center : centre
        - vue : la "vue" de la tour. Classe VueTower par composition
        - xy : coordonnées de la Tour
        - sprite : polygone du canon
        - ennemis : copie de la liste contenant les ennemis
        - enemies_tag : set regroupant les objets avec le tag 'enemy'
        - price : prix de la tour.
    """

    BULLET_VELOCITY = 10

    def __init__(self, canvas, enemies, shooting_range, price, cntr):
        self.c = canvas
        self._shooting_range = shooting_range
        self.center = cntr
        self.vue = VueTower(self.c, self.center)
        self.xy = self.vue.xy
        self.vue.draw_tower(self.center[0], self.center[1])
        self.sprite = self.c.create_polygon(self.xy, fill = "grey", outline = "black")
        self._rayons = [self._distance_to_center(self.xy[i][0], self.xy[i][1]) for i in range(len(self.xy))]
        self._angles = self._find_angles()
        self.enemies = enemies.copy()
        self.enemies_tag  = set(self.c.find_withtag("enemy"))
        self._enemy_order = []
        self._xy0_bullet = [[self.center[0] - 5, self.center[1] - 5],
                           [self.center[0] + 5, self.center[1] + 5]]
        self._can_shoot = False
        self._bullet_out = False

    def _distance_to_center(self, x, y):
        """Détermine la distance d'un point au centre (par Pythagore)."""
        d = sqrt((x - self.center[0])**2 + (y - self.center[1])**2)
        return d

    def _find_angle(self, x, y):
        """Détermine l'angle par rapport au centre."""
        r = self._distance_to_center(x, y)
        dx, dy = x - self.center[0], y - self.center[1]
        ang = acos(dx/r)
        if y < self.center[1]:
            ang *= -1
        return ang

    def _find_angles(self):
        """
        Détermine où se trouve un point sur le cercle centré sur
        self.center.
        """
        angles = []
        for i in range(len(self.xy)):
            r = self._rayons[i]
            a = self.xy[i][0] - self.center[0]
            ang = acos(a/r)
            if self.xy[i][1] < self.center[1]:
                ang *= -1
            angles.append(ang)
        return angles

    def _next_pos_circle(self, rayon, angle, delta):
        """Détermine les coordonnées après un rotation d'un angle 'delta'."""
        x = int(rayon * cos(angle + delta) + self.center[0])
        y = int(rayon * sin(angle + delta) + self.center[1])
        return (x, y)


class FollowTower(ModeleTower):
    """
    Une tour qui est capable de suivre l'ennemi qui dans sa zone de portée.
    La priorité des ennemis est géré ici.

    Attributs :
        - enemy_follow() : suit l'ennemi du regard.
    """

    def __init__(self, canvas, enemies, shooting_range, price, cntr):
        super().__init__(canvas, enemies, shooting_range, price, cntr)
        self.enemy_follow()

    def _is_in_range(self, enemy_center):
        """Détermine si l'ennemi est dans le shooting_range de la tour."""
        a = sqrt((self.center[0] - enemy_center[0])**2 + (self.center[1] - enemy_center[1])**2)
        if a < self._shooting_range:
            return True
        else:
            return False

    def _enemy_priority(self, enemy_center):
        """
        Le premier ennemi vu par la tour est l'ennemi visé jusq'au moment où
        cette troupe n'est plus 'in range' Modification d'une liste, où le
        premier élément a la priorité.
        """
        if self._is_in_range(enemy_center) and self._enemy_order == []:
            self._enemy_order.append(enemy_center)
        elif self._is_in_range(enemy_center) and not self._is_in_range(self._enemy_order[0]):
            del self._enemy_order[0]
            self._enemy_order.append(enemy_center)
        elif not self._is_in_range(enemy_center) and enemy_center in self._enemy_order:
            del self._enemy_order[0]

    def _flatten(self, list_of_lists):
        """
        _flatten one level of nesting.
        https://stackoverflow.com/questions/32449670/tkinter-tclerror-bad-screen
        -distance-in-pythons-tkinter-when-trying-to-modi .
        """
        return itertools.chain.from_iterable(list_of_lists)

    def enemy_follow(self):
        """Suit l'ennemi du regard."""
        for i in range(len(self.enemies)):
            self._enemy_priority(self.enemies[i].center)
        if self._enemy_order != []:
            enemy_center = self._enemy_order[0]
            r = self._distance_to_center(enemy_center[0], enemy_center[1])
            if r < self._shooting_range:
                a = enemy_center[0] - self.center[0]
                ang = acos(a/r)
                if enemy_center[1] < self.center[1]:
                    ang *= -1
                for i in range(len(self._angles)):
                    self.xy[i] = self._next_pos_circle(self._rayons[i], self._angles[i], ang)
                self.c.coords(self.sprite, *self._flatten(self.xy))
        self.c.after(10, self.enemy_follow)


class Tower(FollowTower):
    """
    Une tour capable de suivre et tirer sur les troupes ennemis. Peut
    éliminer les adversaires.

    Attributs :
        - kill_enemy : elimine l'ennemi correspondant.
    """

    DAMAGE = 0.5

    def __init__(self, canvas, enemies, shooting_range, price, cntr):
        super().__init__(canvas, enemies, shooting_range, price, cntr)
        self.shoot()

    def _check_can_shoot(self):
        """
        Ennemi en vue? Si oui change la valeur du boolean 'can_shoot'.
        Crée un polygone 'bullet'.
        """
        if self._enemy_order == []: # aucun ennemi
            self._can_shoot = False
        else:
            self._can_shoot = True
        if self._can_shoot and not self._bullet_out: # ennemi et pas de tirs
            self._bullet_out = True
            self.bullet = self.c.create_oval(self._xy0_bullet,
                                             fill = "gold",
                                             tag = ("bullet"))
            self.c.tag_lower(self.bullet)
            self.c.tag_lower("path")
            self.c.tag_lower("back")

    def _bullet_hit(self):
        """
        Si le bullet touche l'ennemi, alors mettre à jour les points de vie.
        """
        self.enemies[0].hp -= self.DAMAGE
        self.c.delete(self.bullet)
        self._bullet_out = False
        self.enemies[0].update_hp_bar()

    def kill_enemy(self):
        """
        Elimine l'ennemi : met à jour la liste ennemis et enemy_order.
        Ajoute des coins au total.
        """
        coinss = self.enemies[0].coin_return
        self.c.delete(self.enemies[0].sprite)
        self.c.delete(self.enemies[0].hp_bar_box)
        self.enemies[0].alive = False
        self.c.delete(self.enemies[0].hp_bar)
        del self.enemies[0]
        del self._enemy_order[0]
        try:
            self.c.enemies.remove(self.enemies[0])
        except ValueError: # enemy already removed by another tower
            ...
        except IndexError: # enemy does not exist anymore
            self.c.delete(self.bullet)
        else:
            self.c.coins += coinss


    def _enemy_out_of_range(self):
        """Ennemi plus en vue. Met à jour enemies et enemy order."""
        if not self._is_in_range(self.enemies[0].center) and self._enemy_order != []:
            del self.enemies[0]
            del self._enemy_order[0]

    def _move_bullet(self):
        """Deplacement du bullet."""
        dx = self.BULLET_VELOCITY * cos(self.angle)
        dy = self.BULLET_VELOCITY * sin(self.angle)
        self.c.move(self.bullet, dx, dy)

    def shoot(self):
        """
        Tire sur l'ennemi. Déplacement d'ovales de la tour à la troupe
        ennemie.
        """
        self._check_can_shoot()
        if self._bullet_out:
            self._can_shoot = False
            self.coordinates = self.c.coords(self.bullet)
            if self.coordinates != []:
                if self._distance_to_center(self.coordinates[0], self.coordinates[1]) > self._shooting_range:
                    self.c.delete(self.bullet)
            try:
                self.angle = self._find_angle(self._enemy_order[0][0], self._enemy_order[0][1])
                self.collisions = set(self.c.find_overlapping(self.coordinates[0], self.coordinates[1],
                                                              self.coordinates[2], self.coordinates[3]))
            except IndexError:
                self._bullet_out = False
                self.c.delete(self.bullet)
            else:
                self._move_bullet()
                if len(list(self.collisions.intersection(self.enemies_tag))) > 0:
                    self._bullet_hit()
                if self.enemies[0].hp <= 0 and self._enemy_order != []:
                    self.kill_enemy()
                if self.enemies != []:
                    self._enemy_out_of_range()

        if not self._can_shoot:
            self.c.after(15, self.shoot)


class VueLaserBarrier:
    """
    Vue de l'obstacle LaserBarrier.

    Attributs :
        - c : canvas
        - center : centre
        - xy : coordonnées
        - draw_tower : dessine la tour.
    """

    def __init__(self, canvas, center):
        self.c = canvas
        self.center = center
        x, y = self.center
        self.xy = [[x-50,y-30], [x-38,y], [x-25,y-50], [x-13,y], [x,y-50], [x+12,y], [x+25,y-50], [x+37,y], [x+50,y-30]]
        self.xy2 = [[x-50,y+30], [x-38,y], [x-25,y+50], [x-13,y], [x,y+50], [x+12,y], [x+25,y+50], [x+37,y], [x+50,y+30]]
        self.borders = [self.xy[0], self.xy2[8]]

    def draw_tower(self):
        self.c.create_polygon(self.xy, fill = "#7d8cc4")
        self.c.create_polygon(self.xy2, fill = "#7d8cc4")


class LaserBarrier:
    """
    Obstacle qui inflige des dégâts au contact avec l'ennemi. A placer
    uniquement sur les 'paths'.

    Attributs :
        - DAMAGE : quantité de dégâts
        - c : canvas
        - center : centre
        - enemies : copy de la liste enemies
        - xy : coordonées
        - kill_enemy() : tue l'ennemi.
        - enemy_damage() : inflige des dégâts à l'ennemi.
    """

    DAMAGE = 0.1

    def __init__(self, canvas, cntr, enemies, price):
        self.c = canvas
        self.center = cntr
        self.price = price
        self.enemies = enemies.copy()
        self.vue = VueLaserBarrier(self.c, self.center)
        self.xy = self.vue.xy
        self.xy2 = self.vue.xy2
        self.vue.draw_tower()
        self.enemy_damage()

    def _distance_to_center(self, x, y):
        """Détermine la distance d'un point au centre (par Pythagore)."""
        d = sqrt((x - self.center[0])**2 + (y - self.center[1])**2)
        return d

    def kill_enemy(self):
        """
        Elimine l'ennemi : met à jour la liste ennemis et enemy_order.
        Ajoute des coins au total.
        """
        self.c.delete(self.enemies[0].sprite)
        self.c.delete(self.enemies[0].hp_bar_box)
        self.enemies[0].alive = False
        self.c.delete(self.enemies[0].hp_bar)
        del self.enemies[0]
        try:
            self.c.enemies.remove(self.enemies[0])
        except ValueError: # enemy already removed by another tower
            ...
        except IndexError: # enemy does not exist anymore
            ...
        else:
            self.c.coins += self.enemies[0].coin_return

    def enemy_damage(self):
        """Inflige de dégâts à l'ennemi, quand il y a collsion."""
        coordinates = [self.xy[0][0], self.xy[0][1], self.xy2[-1][0], self.xy2[-1][1]]
        self.enemies_tag  = set(self.c.find_withtag("enemy"))
        self.collisions = set(self.c.find_overlapping(coordinates[0],
                                                      coordinates[1],
                                                      coordinates[2],
                                                      coordinates[3]))
        if len(list(self.collisions.intersection(self.enemies_tag))) > 0:
            self.enemies[0].hp -= self.DAMAGE
            self.enemies[0].update_hp_bar()

            if self._distance_to_center(self.enemies[0].center[0], self.enemies[0].center[1]) > 100:
                del self.enemies[0]
        try:
            if self.enemies[0].hp <= 0:
                self.kill_enemy()
        except IndexError:
            ...
        self.c.after(20, self.enemy_damage)


class VueEntrance:
    """Polygones décoratifs pour l'entrée des ennemis."""

    def __init__(self, canvas, center):
        self.center = center
        self.c = canvas
        x, y = self.center
        self.xy2 = [[x-25, y-25], [x-25,y-50], [x+25,y-50], [x+25,y-25], [x+50,y-25], [x+50,y+25], [x+25,y+25], [x+25,y+50], [x-25,y+50], [x-25,y+25], [x-50,y+25], [x-50,y-25]]
        self.xy3 = [[x+25,y-50], [x+25,y-25], [x+50,y-25]]
        self.xy4 = [[x+50,y+25], [x+25,y+25], [x+25,y+50]]
        self.xy6 = [[x-25,y+50], [x-25,y+25], [x-50,y+25]]
        self.xy7 = [[x-50,y-25], [x-25,y-25], [x-25,y-50]]
        self.xy5 = [[x-25,y-25], [x+25, y+25]]
        self.xy8 = [[x, y-25], [x+25,y], [x,y+25], [x-25,y]]
        self.c.create_polygon(self.xy2, fill = "black", tag = ["deco"])
        self.c.create_polygon(self.xy3, fill = "#7d8cc4",tag = ["deco"])
        self.c.create_polygon(self.xy4, fill = "#7d8cc4", tag = ["deco"])
        self.c.create_polygon(self.xy6, fill = "#7d8cc4", tag = ["deco"])
        self.c.create_polygon(self.xy7, fill = "#7d8cc4", tag = ["deco"])
        self.c.create_rectangle(self.xy5, fill = "#7d8cc4", tag = ["deco"])
        self.c.create_polygon(self.xy8, fill = "#eef4ed", tag = ["deco"])


class Enemy:
    """
    Troupe ennemi. Simple polygone qui se déplace au long d'un chemin pré-
    déterminé.

    Attributs :
        - dx : incrément de déplacement de la troupe
        - c : canvas
        - coin_return : la quantité de coins gagné en élimant cette troupe
        - hp : points de vie
        - alive : boolean vrai si hp > 0
        - center : centre
        - xy : coordonnées
        - hp_coords : coordonnées de la barre des points de vie
        - hp_bar : rectangle de la barre de vie
        - sprite : polygone de la troupe

    """


    def __init__(self, canvas, center, hp, coin_return, colour, dx = 1):
        self.dx = dx
        self.c = canvas
        self.hp = hp
        self._hp0 = self.hp
        self.coin_return = coin_return
        self.alive = True
        self.center = center
        x, y = self.center
        self.xy = [[x-12,y+12], [x+12,y-12], [x-12,y-12], [x+12,y+12]]
        self._ymin = self._y_min()
        self.hp_coords = [[self.center[0] - 20, self._ymin - 17],
                          [self.center[0] + 20, self._ymin - 10]]
        self.hp_bar_coords = deepcopy(self.hp_coords)
        self.hp_bar_box = self.c.create_rectangle(self.hp_coords, state = "hidden")
        self.hp_bar = self.c.create_rectangle(self.hp_bar_coords, state = "hidden", fill="red")
        self.sprite = self.c.create_polygon(self.xy, fill = colour, tag = ("enemy"))
        self.moving()
        self.check_damage()

    def calculate_coordinates(self):
        """Détermine le centre de l'objet. À programmer."""
        x, y = self.center
        xy = [[x - 10, y + 10],  [x + 10, y + 10], [x + 10, y - 10], [x - 10, y - 10]]
        return xy

    def _flatten(self, list_of_lists):
        """_flatten one level of nesting. """
        return itertools.chain.from_iterable(list_of_lists)

    def _y_min(self):
        """Retourne le _y_min (utilisé pour les collision)."""
        ymin = 10000
        for i in range(len(self.xy)):
            if self.xy[i][1] < ymin:
                ymin = self.xy[i][1]
        return ymin

    def movex(self):
        """Cheminement de l'ennemi : déplacement en x."""
        for i in range(len(self.xy)):
            self.xy[i][0] += self.dx
        for i in range(len(self.hp_coords)):
            self.hp_coords[i][0] += self.dx
            self.hp_bar_coords[i][0] += self.dx
        self.center[0] += self.dx

    def movey(self):
        """Cheminement de l'ennemi : déplacement en y."""
        for i in range(len(self.xy)):
            self.xy[i][1] -= self.dx
        for i in range(len(self.hp_coords)):
            self.hp_coords[i][1] -= self.dx
            self.hp_bar_coords[i][1] -= self.dx
        self.center[1] -= self.dx

    def moveyneg(self):
        """Cheminement de l'ennemi : déplacement en -y."""
        for i in range(len(self.xy)):
            self.xy[i][1] += self.dx
        for i in range(len(self.hp_coords)):
            self.hp_coords[i][1] += self.dx
            self.hp_bar_coords[i][1] += self.dx
        self.center[1] += self.dx

    def moving(self):
        """Cheminement de l'ennemi, et de sa barre de vie."""
        if self.center[0] < 450 or self.center[1] <= 250 and self.center[0] <= 1150 or self.center[0] >= 1150 and self.center[1] >= 500:
            self.movex()
        elif self.center[0] >= 450 and self.center[0] <= 1150:
            self.movey()
        else:
            self.moveyneg()
        self.c.coords(self.sprite, *self._flatten(self.xy))
        self.c.coords(self.hp_bar_box, *self._flatten(self.hp_coords))
        self.c.coords(self.hp_bar, *self._flatten(self.hp_bar_coords))
        if self.center[0] > self.c.width + 20:
            self.c.counter += 1
            self.c.delete(self.sprite)
            self.c.delete(self.hp_bar_box)
            self.c.delete(self.hp_bar)
            self.alive = False
        if self.alive:
            self.c.after(15, self.moving)

    def check_damage(self):
        """Vérifier dégâts."""
        if self.hp < self._hp0:
            self.c.itemconfig(self.hp_bar_box, state = "normal")
            self.c.itemconfig(self.hp_bar, state = "normal")
        self.c.after(100, self.check_damage) # pas besoin de vérifier tout le temps

    def update_hp_bar(self):
        """Changer la barre de points de vie proportionellement."""
        prop = self.hp/self._hp0
        delta_x = abs(self.hp_coords[1][0] - self.hp_coords[0][0])
        self.hp_bar_coords[1][0] = self.hp_bar_coords[0][0] + prop * delta_x
        self.c.coords(self.hp_bar, *self._flatten(self.hp_bar_coords))


class TowerHologramSpawner:

    """
    Une 'sorte' de bouton qui sur click créera un hologramme d'une tour.
    L'holograme sera créé sur 'click', puis pourra être déplacé et déposé à l'
    endroit voulu. Il est ensuite détruit et remplacé par une vraie tour de
    défense (classTower). Interface drag and drop.
    """

    def __init__(self, root, canvas, enemies, price, center):
        self.c = canvas
        self.root = root
        self.price = price
        self.enemies = enemies.copy()
        self.center = center
        self.hol_center = self.center.copy()
        self.vue = VueTower(self.c, self.center)
        self.draw_spawner()
        self.spawner = self.c.create_rectangle(self.xy, fill = "black", tag = ["spawn"], activefill="yellow")
        self.c.tag_bind(self.spawner, "<1>", self.create_hologram)

    def draw_spawner(self):
        """Calcule les coordonnées du polygone relatif au centre."""
        x, y = self.center
        self.xy = [x-25, y-25, x+25, y+25]
        self.vue.draw_tower(self.center[0], self.center[1], spawn = True)

    def create_hologram(self, event):
        """Création d'une image hologramme."""
        self.root.img = img = tk.PhotoImage(file = "data/yo.png").subsample(2)
        self.hologram = self.c.create_image(self.center, image=img)
        self.c.tag_bind(self.hologram, "<B1-Motion>", self.drag_hologram)

    def drag_hologram(self, event):
        self.c.tag_bind(self.hologram, "<ButtonRelease-1>", self.drop_hologram)
        self.hol_center = [event.x, event.y]
        self.c.coords(self.hologram, self.hol_center)

    def drop_hologram(self, event):
        self.c.delete(self.hologram)
        if self.c.coins >= self.price:
            vue = VueTower(self.c, self.hol_center)
            coordinates = vue.borders
            collisions = set(self.c.find_overlapping(coordinates[0], coordinates[1],
                                                     coordinates[2], coordinates[3]))
            self.path_tag  = set(self.c.find_withtag("path"))
            self.tower_tag = set(self.c.find_withtag("tower"))
            self.collisions_tag = self.path_tag.union(self.tower_tag)
            if len(list(collisions.intersection(self.collisions_tag))) <= 0:
                Tower(self.c, self.enemies, shooting_range = 200, price = self.price, cntr = self.hol_center)
                self.c.coins -= self.price


class LaserBarrierSpawner:


    def __init__(self, root, canvas, enemies, price, center):
        self.c = canvas
        self.root = root
        self.price = price
        self.enemies = enemies.copy()
        self.center = center
        self.hol_center = self.center.copy()
        self.vue = VueLaserBarrier(self.c, self.center)
        self.spawner = self.c.create_polygon(self.vue.xy, activefill="yellow", fill = "#7d8cc4")
        self.spawner2 = self.c.create_polygon(self.vue.xy2, activefill="yellow", fill = "#7d8cc4")
        self.c.tag_bind(self.spawner, "<1>", self.create_hologram)
        self.c.tag_bind(self.spawner2, "<1>", self.create_hologram)

    def create_hologram(self, event):
        self.root.img2 = img2 = tk.PhotoImage(file = "data/yo2.png").subsample(2)
        self.hologram = self.c.create_image(self.center, image=img2)
        self.c.tag_bind(self.hologram, "<B1-Motion>", self.drag_hologram)

    def drag_hologram(self, event):
        self.c.tag_bind(self.hologram, "<ButtonRelease-1>", self.drop_hologram)
        self.hol_center = [event.x, event.y]
        self.c.coords(self.hologram, self.hol_center)

    def drop_hologram(self, event):
        self.c.delete(self.hologram)
        if self.c.coins >= self.price:
            vue = VueLaserBarrier(self.c, self.hol_center)
            coordinates = vue.borders
            collisions = set(self.c.find_overlapping(coordinates[0][0], coordinates[0][1],
                                                     coordinates[1][0], coordinates[1][1]))
            self.path_tag  = set(self.c.find_withtag("path"))
            if len(list(collisions.intersection(self.path_tag))) > 0:
                LaserBarrier(self.c, self.hol_center, self.enemies, 200)
                self.c.coins -= self.price


class GameCanvas(tk.Canvas):
    """Canvas principal du jeu. Controle."""

    def __init__(self, master):
        self.master = master
        self.width = 1270
        self.height = 790
        super().__init__(master,
                         width = self.width,
                         height = self.height,
                         bd = 1,
                         highlightthickness=0,
                         bg = "#bee7e8")
        self.coins = 500
        self.enemies = []
        self.x = -500
        self.counterminusone = 0
        self.counter = 0
        self.wavecounter = 0
        self.launched = False
        self.menu(None)

    def menu(self, event):
        """
        Menu du jeu avec un bouton 'mystère': soit le menu d'aide, soit le
        jeu, soit l'arrêt du jeu !
        """
        self.master.master.title = title = tk.PhotoImage(file = "data/finito.png").subsample(2)
        self.titre = self.create_image(self.width/2, 110, image=title, anchor = "n")
        self.start = self.create_polygon(
                                         530, 410, #cor2
                                         740, 410, #cor3
                                         720, 455,#cor4
                                         740, 500,#cor6
                                         530, 500,#cor7
                                         550, 455, #cor8
                                         fill="#7d8cc4",
                                         width = 2,
                                         tag =["hihi"],
                                         activefill = "#eef4ed")
        self.design = self.create_rectangle(0, 600, self.width, 700, outline = "", fill = "#594157", tag = ["path", "horizontal"])
        self.st = VueEntrance(self, [0, 650])
        self.ed = VueEntrance(self, [self.width, 650])
        self.txt = self.create_text(635, 455, text = "Play", font=("Purisa", "23"))
        self.functions = (self.jeu, self.help, self.master.master.kill)
        self.tag_bind(self.start, "<1>",self.jeu)

    def delete_menu(self):
        """Supprime l'UI du menu."""
        self.delete(self.titre)
        self.delete("deco")
        self.delete(self.design)
        self.delete(self.start)
        self.delete(self.txt)
        self.delete(self.design)

    def help(self, event):
        """Le menu d'aide."""
        self.delete_menu()
        self.master.master.bind("<b>", self.delete_help_menu)
        self.master.master.help = help = tk.PhotoImage(file = "data/eguhelp.png").subsample(2)
        self.help_text = self.create_image(0, 0, image=help, anchor = "nw")

    def delete_help_menu(self, event):
        self.delete(self.help_text)
        self.menu(None)

    def jeu(self, event):
        """Le jeu principal."""
        self.delete_menu()
        self.box = self.create_rectangle(975, 50, 1090, 105, fill = "#a0d2db", outline="black")
        self.coin_text = self.create_text(1025, 77, text=self.coins, anchor = "w", font=("Purisa", "20"))
        self.master.master.coin = coin = tk.PhotoImage(file = "data/coinpnggg.png").subsample(33)
        self.hologram = self.create_image(950, 48, image=coin, anchor = "nw")
        self.waves()
        self.draw_path()
        self.check_danger()
        self.check_coins()

        TowerHologramSpawner(self.master.master, self, self.enemies, 200, [100, 100])
        self.create_text(100, 155, text="200 eGus", anchor = "n", font=("Purisa", "20"))
        LaserBarrierSpawner(self.master.master, self, self.enemies, 100, [250, 100])
        self.create_text(250, 155, text="100 eGus", anchor = "n", font=("Purisa", "20"))

    def draw_path(self):
        """Rectangles formant le chemin suivi par les ennemis."""
        VueEntrance(self, [0, 650])
        self.xy1 = [[0, 600], [0, 700], [400, 700], [400, 600]]
        self.create_polygon(self.xy1, outline = "", fill = "#594157", tag = ["path", "horizontal"])
        self.xy2 = [[400, 200], [400, 700], [500, 700], [500, 200]]
        self.create_polygon(self.xy2, outline = "", fill = "#594157", tag = ["path"])
        self.xy3 = [[500, 200], [500, 300], [1100, 300], [1100, 200]]
        self.create_polygon(self.xy3, outline = "", fill = "#594157", tag = ["path", "horizontal"])
        self.xy4 = [[1100, 200], [1100, 550], [1200, 550], [1200, 200]]
        self.create_polygon(self.xy4, outline = "", fill = "#594157", tag = ["path"])
        self.xy5 = [1200, 450], [1200, 550], [1270, 550], [1270, 450]
        self.create_polygon(self.xy5, outline = "", fill = "#594157", tag = ["path", "horizontal"])
        VueEntrance(self, [1270, 500])
        self.tag_lower("path")

    def check_danger(self):
        """Verification de danger et GAMEOVER."""
        if self.counterminusone < self.counter:
            self.config(bg = "#FF6978")
            self.update()
            self.counterminusone += 1
            self.after(5000)
            self.delete("all")
            self.master.master.gamov = gamov = tk.PhotoImage(file = "data/gamov.png").subsample(2)
            self.hologram = self.create_image(self.width/2, self.height/2, image=gamov)
            self.update()
            self.after(5000)
            self.master.master.kill(None)
        self.after(100, self.check_danger)

    def check_coins(self):
        self.itemconfigure(self.coin_text, text = self.coins)
        self.after(100, self.check_coins)

    def waves(self):
        self.wave1()
        self.wave2()
        self.wave3()
        self.wave4()

    def wave1(self):
        for i in range(7):
            self.enemies.append(Enemy(self, [self.x, 650], hp = 20, coin_return = 20, colour = "#BAFF29"))
            self.x -= 250

    def wave2(self):
        self.x -= 250
        for i in range(50):
            self.enemies.append(Enemy(self, [self.x, 650], hp = 5, coin_return = 7, colour = "#20A4F3"))
            if i % 10 == 0:
                self.x -= 250
            else:
                self.x -= 10

    def wave3(self):
        self.x -= 250
        for i in range(1):
            self.enemies.append(Enemy(self, [self.x, 650], hp = 100, coin_return = 100, colour = "#DB5ABA"))
            self.x -= 500

    def wave4(self):
        self.x -= 250
        for i in range(50):
            self.enemies.append(Enemy(self, [self.x, 650], hp = 5, coin_return = 7, colour = "#FED766"))
            if i % 10 == 0:
                self.x -= 250
            else:
                self.x -= 10


class Background(tk.Frame):

    def __init__(self, master):
        self.width = master.master.winfo_screenwidth()
        self.height = master.master.winfo_screenheight()
        super().__init__(master,
                         width = self.width,
                         height = self.height,
                         bg = "#594157")


class Vue(tk.Frame):

    def __init__(self, master):
        self.master = master
        super().__init__(master, bg = "black")
        self.background = Background(self)
        self.gamescreen = GameCanvas(self)
        self.background.grid()
        self.gamescreen.grid(column = 0, row=0)
        self.grid()


class Controle(tk.Tk):

    def __init__(self):
        super().__init__()
        self.title("eGu8g")
        self["bg"] = "black"
        self.attributes("-fullscreen", True)
        self.vue = Vue(self)
        self.bind("q", self.kill)

    def kill(self, event):
        self.destroy()


if __name__ == "__main__":
    Controle().mainloop()
