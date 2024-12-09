// Copyright (c) Microsoft Corporation.
// Licensed under the MIT License.

using UnityEngine;
using MLAgents;
using System;
using System.Collections;
using System.Collections.Generic;
using WindowsInput; 
using WindowsInput.Native;

public class PinballAgent : Agent
{
    [Header("Specific to Pinball")]
    PinballAcademy m_Academy;

    public float TimeBetweenDecisionsAtInference;
    private float m_TimeSinceDecision;

    public Func<bool> GameHasEnded;
    private List<int> actionMask;

    private int previousBall = 0;
    private long previousScore = 0;

    public override void InitializeAgent()
    {
        m_Academy = FindObjectOfType(typeof(PinballAcademy)) as PinballAcademy;

        if (GameHasEnded == null)
        {
            GameHasEnded = () =>
            {
                //If ball is 0 then game is over
                return (ExternalWindowManager.Ball == 0);
            };
        }
        actionMask = new List<int>(new[] {
            0, //Disable Idle
            //1, //Disable Z press
            //2, //Disable z release
            //3, //Disable / press
            //4, //Disable / release
            //5, //Disable Space press
            //6, //Disable Space release 
        });
        SetActionMask(actionMask);
    }

    public override void CollectObservations()
    {
        AddVectorObs(ExternalWindowManager.Ball);
        AddVectorObs(ExternalWindowManager.Score);
    }

    public override void AgentAction(float[] vectorAction)
    {
        // Perform choosen action
        var action = (int)vectorAction[0];

        InputSimulator inputSimulator = new InputSimulator();

        // Simulate key press
        switch (action)
        {
            case 0:
                Debug.Log("Idle action");
                break;
            case 1:
                StartCoroutine(SimulateKeyPress(inputSimulator, VirtualKeyCode.LSHIFT, 0.1f)); // Left flipper
                Debug.Log("Left flipper pressed");
                break;
            case 2:
                StartCoroutine(SimulateKeyPress(inputSimulator, VirtualKeyCode.RSHIFT, 0.1f)); // Right flipper
                Debug.Log("Right flipper pressed");
                break;
            case 3:
                StartCoroutine(SimulateKeyPress(inputSimulator, VirtualKeyCode.RETURN, 0.2f)); // Plunger
                Debug.Log("Plunger pressed");
                break;
            default:
                Debug.LogError("Unknown action: " + action);
                break;
        }
        actionMask.Sort();
        SetActionMask(actionMask);

        //// Add rewards
        //1) Score
        if (previousScore < ExternalWindowManager.Score) // Get the difference between last score (from last descision) and current score.
        {
            //Small benefit score is going up. 
            //Assume max score 999,999,999 however, each step max will only be a fraction of that.
            AddReward(0.00001f * (ExternalWindowManager.Score - previousScore)); //Small 2k large 20k, not sure what largest bonus is but this will do.
        }
        else
        {
            //No score change add negative reward (aka punish);
            AddReward(-0.00001f); //-0.00001f is a small negative but should encourage more activity
        }
        // Set previous score;
        previousScore = ExternalWindowManager.Score;

        //2) Ball
        if (previousBall < ExternalWindowManager.Ball)
        {
            Debug.Log("Dropped Ball:" + previousBall);
            if (previousBall != 0) // If we drop a ball thats is not game over or starting ball.
            {
                AddReward(-0.03f); // Droped the ball add negative reward (aka punish); -0.3 is pretty bad. Thats like 30k in points.
            }

            //reset keys
            ResetKeys();
        }

        // Set previous score;
        previousBall = ExternalWindowManager.Ball;
        
        //Monitor
        Monitor.SetActive(true);
        Monitor.Log("Reward:", GetReward().ToString());
        Monitor.Log("Cumulative Reward:", GetCumulativeReward().ToString());

        //// End a training episode
        // End game logic
        if (GameHasEnded())
        {
            // Reward the agent for end of round.
            // I think this is confusing the training, I think use below OR use score step diff (line 103-110)
            //SetReward(0.000000001f * ExternalWindowManager.Score); // Read the scoreboard. Assume max score 999,999,999
            Debug.Log($"Game Ended Score: {ExternalWindowManager.Score} | Total Reward: {GetCumulativeReward().ToString()}");

            // Press 1 button to start new game
            inputSimulator.Keyboard.KeyPress(VirtualKeyCode.VK_1); 

            // // If high score press enter
            // ExternalWindowManager.PressKey(0x0D); //f2
            // ExternalWindowManager.PressKey(0x0D, true); //f2 

            // Reset reward
            previousScore = 0;
            previousBall = 0;

            //reset keys
            ResetKeys();

            // Tell agent to reset
            Done();
        }
    }

    public void ResetKeys()
    {

        InputSimulator inputSimulator = new InputSimulator();

        inputSimulator.Keyboard.KeyUp(VirtualKeyCode.LSHIFT);
        inputSimulator.Keyboard.KeyUp(VirtualKeyCode.RSHIFT);
        inputSimulator.Keyboard.KeyUp(VirtualKeyCode.RETURN); //enter

        actionMask = new List<int>(new[] {
                0, //Disable Idle
                //1, //Disable Z press
                //2, //Disable z release
                //3, //Disable / press
                //4, //Disable / release
                //5, //Disable Space press
                //6, //Disable Space relaease 
            });
        SetActionMask(actionMask);
    }

    public override void AgentReset()
    {

    }

    public override float[] Heuristic()
    {
        return new float[] { 0 };
    }

    public void FixedUpdate()
    {
        WaitTimeInference();
    }

    void WaitTimeInference()
    {
        //if (!m_Academy.GetIsInference())
        //{

        //    RequestDecision();
        //}
        //else
        //{
        if (m_TimeSinceDecision >= TimeBetweenDecisionsAtInference)
        {
            m_TimeSinceDecision = 0f;
            RequestDecision();
        }
        else
        {
            m_TimeSinceDecision += Time.fixedDeltaTime;
        }
        //}
    }

    // Coroutine to simulate a key press for a specific duration
    private IEnumerator SimulateKeyPress(InputSimulator inputSimulator, VirtualKeyCode keyCode, float duration)
    {
        inputSimulator.Keyboard.KeyDown(keyCode);
        yield return new WaitForSeconds(duration);
        inputSimulator.Keyboard.KeyUp(keyCode);
    }
}
