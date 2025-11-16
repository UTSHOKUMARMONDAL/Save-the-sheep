from flask import Flask, render_template, request
import random

app = Flask(__name__)


def move_position(pos, move, grid, ROWS, COLS):
    x, y = pos
    new_x, new_y = x, y

    if move == "up" and x > 0:
        new_x -= 1
    elif move == "down" and x < ROWS - 1:
        new_x += 1
    elif move == "left" and y > 0:
        new_y -= 1
    elif move == "right" and y < COLS - 1:
        new_y += 1

    # Tiger block
    if grid[new_x][new_y] == "T":
        return pos

    return (new_x, new_y)


def fitness(chromosome, grid, start_pos, home_pos, ROWS, COLS, MAX_STEPS):
    pos = start_pos
    coins = 0
    visited_coins = set()
    steps = 0
    reached_home = False

    for move in chromosome:
        new_pos = move_position(pos, move, grid, ROWS, COLS)

        if new_pos == pos:
            continue

        pos = new_pos
        steps += 1

        if grid[pos[0]][pos[1]] == "C" and pos not in visited_coins:
            coins += 1
            visited_coins.add(pos)

        if grid[pos[0]][pos[1]] == "H":
            reached_home = True
            break

        if steps >= MAX_STEPS:
            break

    if not reached_home:
        dist = abs(pos[0] - home_pos[0]) + abs(pos[1] - home_pos[1])
        return coins * 20 - dist * 10

    return coins * 100 + (MAX_STEPS - steps) * 10


def random_chromosome(moves, MAX_STEPS):
    return [random.choice(moves) for _ in range(MAX_STEPS)]


def selection(pop, fitness_func):
    pop = sorted(pop, key=lambda x: fitness_func(x), reverse=True)
    return pop[:len(pop)//2]


def crossover(p1, p2, MAX_STEPS):
    point = random.randint(1, MAX_STEPS - 2)
    return p1[:point] + p2[point:], p2[:point] + p1[point:]


def mutate(chrom, moves, MUTATION_RATE, MAX_STEPS):
    if random.random() < MUTATION_RATE:
        chrom[random.randint(0, MAX_STEPS - 1)] = random.choice(moves)
    return chrom


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/run', methods=['POST'])
def run_algorithm():
    MAX_STEPS = int(request.form['max_steps'])
    ROWS = int(request.form['rows'])
    COLS = int(request.form['cols'])

    grid_input = request.form['grid'].strip().split('\n')
    grid = [row.strip().split() for row in grid_input]

    start_pos, home_pos = None, None

    for i in range(ROWS):
        for j in range(COLS):
            if grid[i][j] == "S":
                start_pos = (i, j)
            elif grid[i][j] == "H":
                home_pos = (i, j)

    if not start_pos or not home_pos:
        return "Grid must contain 'S' and 'H'."

    moves = ["up", "down", "left", "right"]
    POP_SIZE = 60
    GENERATIONS = 200
    MUTATION_RATE = 0.25

    population = [random_chromosome(moves, MAX_STEPS) for _ in range(POP_SIZE)]
    best_path = None
    best_fit = float('-inf')

    # GA loop
    for _ in range(GENERATIONS):
        fitness_func = lambda chrom: fitness(
            chrom, grid, start_pos, home_pos, ROWS, COLS, MAX_STEPS
        )

        population = selection(population, fitness_func)

        next_gen = []
        while len(next_gen) < POP_SIZE:
            p1, p2 = random.sample(population, 2)
            c1, c2 = crossover(p1, p2, MAX_STEPS)

            next_gen.append(mutate(c1, moves, MUTATION_RATE, MAX_STEPS))
            if len(next_gen) < POP_SIZE:
                next_gen.append(mutate(c2, moves, MUTATION_RATE, MAX_STEPS))

        population = next_gen

        for chrom in population:
            fit = fitness(chrom, grid, start_pos, home_pos, ROWS, COLS, MAX_STEPS)
            if fit > best_fit:
                best_fit = fit
                best_path = chrom


    pos = start_pos
    grid_path = [row[:] for row in grid]
    executed_moves = []
    coins_collected = 0
    steps_taken = 0
    home_reached = False
    visited_final = set()  

    for move in best_path:
        new_pos = move_position(pos, move, grid, ROWS, COLS)

        if new_pos == pos:
            continue

        executed_moves.append(move)
        pos = new_pos
        steps_taken += 1

        x, y = pos

        if grid[x][y] == "C":
            if (x, y) not in visited_final:
                coins_collected += 1
                visited_final.add((x, y))
                grid_path[x][y] = "**"

        elif grid[x][y] == "H":
            home_reached = True
            grid_path[x][y] = "H"
            break

        elif grid_path[x][y] not in ["S", "T"]:
            grid_path[x][y] = "*"

        if steps_taken >= MAX_STEPS:
            break

    best_path_str = " → ".join(executed_moves)

    return render_template(
        'result.html',
        grid=grid_path,
        best_path=best_path_str,
        score=best_fit,
        coins=coins_collected,
        steps=steps_taken,
        reached=home_reached
    )


if __name__ == "__main__":
    app.run(debug=True)
