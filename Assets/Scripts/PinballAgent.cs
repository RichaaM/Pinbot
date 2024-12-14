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

    private Coroutine plungerCoroutine;

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
        // SetActionMask(actionMask);

        // Start the plunger loop
        if (plungerCoroutine == null)
        {
            plungerCoroutine = StartCoroutine(PlungerLoop());
        }
    }

    private IEnumerator PlungerLoop()
    {
        InputSimulator inputSimulator = new InputSimulator();

        while (true)
        {
            // Debug.Log("Pulling back plunger...");
            // pull back the plunger using the enter key
            inputSimulator.Keyboard.KeyDown(VirtualKeyCode.RETURN);
            yield return new WaitForSecondsRealtime(1.0f);
            // Debug.Log("Releasing plunger...");
            
            inputSimulator.Keyboard.KeyUp(VirtualKeyCode.RETURN);
            yield return new WaitForSecondsRealtime(0.5f);

        }
    }

    public override void CollectObservations()
    {
        // AddVectorObs(ExternalWindowManager.Ball);
        // AddVectorObs(ExternalWindowManager.Score);
        // Add the ball position and velocity, normalizing to a range of 0 to 1
        AddVectorObs(ExternalWindowManager.PoseX/2000.0f);
        AddVectorObs(ExternalWindowManager.PoseY/2000.0f);
        AddVectorObs(ExternalWindowManager.VelX/2000.0f); 
        AddVectorObs(ExternalWindowManager.VelY/2000.0f); 
    }

    public override void AgentAction(float[] vectorAction)
    {
        // Perform choosen action
        var action = (int)vectorAction[0];

        InputSimulator inputSimulator = new InputSimulator();

        // raise keys if down
        if (inputSimulator.InputDeviceState.IsKeyDown(VirtualKeyCode.LSHIFT))
        {
            inputSimulator.Keyboard.KeyUp(VirtualKeyCode.LSHIFT);
        }
        if (inputSimulator.InputDeviceState.IsKeyDown(VirtualKeyCode.RSHIFT))
        {
            inputSimulator.Keyboard.KeyUp(VirtualKeyCode.RSHIFT);
        }

        // Simulate key press
        switch (action)
        {
            case 0:
                // Debug.Log("Idle action");
                break;
            case 1:
                inputSimulator.Keyboard.KeyDown(VirtualKeyCode.LSHIFT);
                // Debug.Log("Left flipper pressed");
                break;
            case 2:
                inputSimulator.Keyboard.KeyDown(VirtualKeyCode.RSHIFT);
                // Debug.Log("Right flipper pressed");
                break;
            case 3:
                inputSimulator.Keyboard.KeyDown(VirtualKeyCode.LSHIFT);
                inputSimulator.Keyboard.KeyDown(VirtualKeyCode.RSHIFT);
                // Debug.Log("Both flippers pressed");
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
            // Debug.Log("Score increased: " + (ExternalWindowManager.Score - previousScore));
            //Small benefit score is going up. 
            //Assume max score 999,999,999 however, each step max will only be a fraction of that.
            AddReward(0.00003f * (ExternalWindowManager.Score - previousScore)); //Small 2k large 20k, not sure what largest bonus is but this will do.
        }
        else
        {
            //No score change add negative reward (aka punish);
            AddReward(-0.00001f); //-0.00001f is a small negative but should encourage more activity
        }
        // Set previous score;
        previousScore = ExternalWindowManager.Score;

        //2) Location
        // If the ball is in the air (above the flippers), give a small reward
        // This is to encourage the agent to keep the ball in the air
        // 1400 is just above the flippers. Lower values are higher up.
        if (ExternalWindowManager.PoseY < 1400.0f)
        {
            AddReward(0.005f); //Small reward for keeping the ball in the air
        }

        //3) Ball
        if (previousBall < ExternalWindowManager.Ball && ExternalWindowManager.Ball == 9) 
        {
            // Debug.Log("Dropped Ball:" + previousBall);
            if (previousBall != 0) // If we drop a ball that's not the starting ball.
            {
                // Debug.Log("Applying penalty:");
                AddReward(-0.3f); // Dropped the ball, add negative reward (aka punish); -0.3 is pretty bad. That's like 30k in points.
                // wait a second
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
        Monitor.Log("Ball:", ExternalWindowManager.Ball.ToString());
        Monitor.Log("Score:", ExternalWindowManager.Score.ToString());

        //// End a training episode
        // End game logic
        if (GameHasEnded())
        {
            // Reward the agent for end of round.
            // I think this is confusing the training, I think use below OR use score step diff (line 103-110)
            //SetReward(0.000000001f * ExternalWindowManager.Score); // Read the scoreboard. Assume max score 999,999,999
            // Debug.Log($"Game Ended Score: {previousScore} | Total Reward: {GetCumulativeReward().ToString()}");

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
        if (plungerCoroutine != null)
        {
            StopCoroutine(plungerCoroutine);
            plungerCoroutine = StartCoroutine(PlungerLoop());
        }
    }

    private void OnDisable()
    {
        // Clean up coroutine to avoid memory leaks
        if (plungerCoroutine != null)
        {
            StopCoroutine(plungerCoroutine);
        }
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
}
