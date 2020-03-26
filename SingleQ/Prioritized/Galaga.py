#!/usr/bin/env python3

# Basal program for the Single Q-Learning Prioritized Replay implementation

import sys
from gym import core, spaces
import retro
import numpy as np

sys.path.append('../../') # Get top-level
from HyperParameters import *
from utils import preprocess, map_actions
from GalagaAgent import GalagaAgent
from ReplayMemory import ReplayMemory

def main():

    env = retro.make(game=params['ENVIRONMENT'],
                     use_restricted_actions=retro.Actions.DISCRETE)

    action_space = env.action_space.n if params['USE_FULL_ACTION_SPACE'] else params['SMALL_ACTION_SPACE']
    env.action_space = spaces.Discrete(action_space)
    epsilon = params['EPSILON']
    epsilon_gamma = params['EPSILON_GAMMA']
    epsilon_min = params['EPSILON_MIN']
    epochs = params['EPOCHS']
    epoch_length = params['EPOCH_MAX_LENGTH']
    use_time_cutoff = params['USE_TIME_CUTOFF']

    img_width = params['IMG_WIDTH']
    img_height = params['IMG_HEIGHT']
    channels = 1 if params['GRAYSCALE'] else 3
    input_space = (env.observation_space.shape[0])

    replay_iterations = params['REPLAY_ITERATIONS']
    replay_sample_size = params['REPLAY_SAMPLE_SIZE']
    replay_memory_size = params['REPLAY_MEMORY_SIZE']
    replay_alpha = params['REPLAY_ALPHA']

    q_learning_gamma = params['Q_LEARNING_GAMMA']
    frames_since_score_limit = params['FRAMES_SINCE_SCORE_LIMIT']

    model = GalagaAgent(action_space, img_width, img_height, channels)
    target = GalagaAgent(action_space, img_width, img_height, channels)

    memory = ReplayMemory(replay_memory_size, img_width, img_height, channels, action_space)

    for epoch in range(epochs):
        state = env.reset();
        done = False
        time_since_score_up = 0
        last_score = 0
        time = 0

        while not done:
            state = preprocess(state, img_width, img_height, channels)
            chance = np.random.random()
            if chance > epsilon:
                action, model_Q = model.get_action(state)
            else:
                action, model_Q = map_actions(np.random.randint(0, action_space)), None

            next_state, reward, done, info = env.step(action)

            # Reward
            if info['score'] == last_score:
                time_since_score_up += 1
            else:
                time_since_score_up = 0

            if time_since_score_up >= frames_since_score_limit:
                reward -= 1

            last_score = info['score']

            # Memory Replay

            pp_next = preprocess(next_state, img_width, img_height, channels)

            if not type(model_Q) is np.ndarray:
                model_Q = model.predict(state)

            target_Q = target.predict(pp_next)
           
            td_error = memory.td_error(model_Q,
                                       target_Q,
                                       reward,
                                       q_learning_gamma)

            memory.remember(state,
                            int(action/3),
                            reward,
                            pp_next,
                            done,
                            td_error)

            state = next_state

            if use_time_cutoff and time > epoch_length:
                break

            if "--play" in sys.argv:
                env.render()

            time += 1

        memory.replay(model, target, replay_sample_size, q_learning_gamma, replay_alpha)
        epsilon = epsilon * epsilon_gamma if epsilon > epsilon_min else epsilon_min

        score_window.append(info['score'])
        mean_score = np.mean(score_window)

        print("\r Episode: %d/%d, Epsilon: %f, Mean Score: %d" % (epoch+1, epochs, epsilon, mean_score))

if __name__ == "__main__":
    np.random.seed(params['NUMPY_SEED'])
    main()
