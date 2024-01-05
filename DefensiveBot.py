from tools import *
from objects import *
from routines import *

# This file contains the strategy for a defensive training bot for 1v1 Rocket League matches.
# The strategy is supported by GoslingUtils and GoslingUtils Examples.

class DefensiveBot(GoslingAgent):
    """
    DefensiveBot is a defensive training bot designed for 1v1 Rocket League matches.
    It makes decisions based on the positions of the ball, the opponent, and itself.
    """

    def run(agent):
        """
        The main function called every tick to determine the bot's actions.
        It involves decision-making for defense and offense based on the game state.
        """

        # Determine if the ball is closer to our goal than the bot.
        # This helps in deciding whether to defend or to take a more aggressive position.

        ball_dist_to_owngoal = (agent.ball.location - agent.friend_goal.location).magnitude()
        my_dist_to_owngoal = (agent.me.location - agent.friend_goal.location).magnitude()
        ball_closer_than_me = ball_dist_to_owngoal < my_dist_to_owngoal

        # Determine if the opponent is closer to the ball than the bot.
        # This information is used to assess the urgency of defensive action.

        opponent_closer_than_me = False
        if len(agent.foes) > 0:
            opponent_dist_to_ball = (agent.foes[0].location - agent.ball.location).magnitude()
            my_dist_to_ball = (agent.me.location - agent.ball.location).magnitude()
            opponent_closer_than_me = opponent_dist_to_ball < my_dist_to_ball

        def find_best_boost(agent):
            """
            Determines the best boost to go for based on the current game state.
            Considers boost pad positions and whether they are active.
            """

            # The function evaluates available boost pads and selects the most suitable one.
            
            best_boost = None
            best_boost_score = -1.0

            for boost in agent.boosts:
                if not boost.active:
                    continue

                # Scoring of boost pads based on their position relative to the bot and the goal.
                me_to_boost = (boost.location - agent.me.location).normalize()
                boost_to_goal = (agent.friend_goal.location - boost.location).normalize()
                boost_score = boost_to_goal.dot(me_to_boost)

                # Prefers large boosts but will consider small boosts if they are strategically placed.
                if boost.large or (boost_score > best_boost_score + 0.2):
                    if boost_score > best_boost_score:
                        best_boost_score = boost_score
                        best_boost = boost

            return best_boost
        
        def return_to_net(agent, target):
            """
            Manages the bot's movement back to the net for defense.
            Uses default PD and Throttle for the movement.
            """
            # Calculates the path to return to the net and uses standard driving functions to execute.
            relative_target = target - agent.me.location
            distance = relative_target.magnitude()
            local_target = agent.me.local(relative_target)
            defaultPD(agent, local_target)
            defaultThrottle(agent, cap(distance * 2, 0, 2300))

        def standard_defense(agent):
            """
            Implements the standard defensive strategy of the bot.
            Decides whether to collect boost or directly return to the net based on various conditions.
            """
            # The bot decides to collect boost or return directly based on its current boost amount and ball position.
            if agent.me.boost > 24:
                return_to_net(agent, agent.friend_goal.location)
            else:
                if ball_dist_to_owngoal + 200 < my_dist_to_owngoal:
                    return_to_net(agent, agent.friend_goal.location)
                else:
                    best_boost = find_best_boost(agent)
                    if best_boost:
                        agent.push(goto_boost(best_boost, agent.friend_goal.location))
                    return_to_net(agent, agent.friend_goal.location)

        # Main decision-making for handling routines.
        if len(agent.stack) < 1:
            if agent.kickoff_flag:
                best_boost = find_best_boost(agent)
                if best_boost:
                    agent.push(goto_boost(best_boost, agent.friend_goal.location))
                return_to_net(agent, agent.friend_goal.location)
            else:
                # Targeting system for offensive and clear shots.
                targets = {
                    "clear": (Vector3(-4100 * side(agent.team), agent.ball.location.y, 0), Vector3(4100 * side(agent.team), agent.ball.location.y, 0))
                }

                # Identifying potential shots based on the game state.
                shots = find_hits(agent, targets)
                
                if opponent_closer_than_me:
                    if ball_closer_than_me:
                        # Defensive strategy when the opponent is closer to the ball and the ball is near our goal.
                        standard_defense(agent)
                    else:
                        # Offensive play if the bot has a chance to take a shot or clear the ball.
                        if len(shots["clear"]) > 0:
                            agent.push(shots["clear"][0])
                        else:
                            agent.push(short_shot(agent.foe_goal.location))

                elif ball_closer_than_me:
                    # Standard defense if the ball is closer to our goal.
                    standard_defense(agent)
                    if len(shots["clear"]) > 0:
                        agent.push(shots["clear"][0])
                    
                else:
                    # Offensive play when the defensive positioning is optimal.
                    agent.push(short_shot(agent.foe_goal.location))