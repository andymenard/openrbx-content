-- Drive the four Motor joints created by the OpenRBX humanoid.
local character = script.Parent
local torso = character.Torso
local humanoid = character.Humanoid
local rightShoulder = torso["Right Shoulder"]
local leftShoulder = torso["Left Shoulder"]
local rightHip = torso["Right Hip"]
local leftHip = torso["Left Hip"]
local speed = 0
local climbing = false
local jumping = false
local falling = false
local phase = 0

humanoid.Running:connect(function(value)
    speed = value
    climbing = false
end)

humanoid.Climbing:connect(function(value)
    speed = value
    climbing = true
end)

humanoid.Jumping:connect(function(active)
    jumping = active
end)

humanoid.FreeFalling:connect(function(active)
    falling = active
end)

game:GetService("RunService").Stepped:connect(function(time, step)
    local arm = 0
    local leg = 0
    if jumping or falling then
        arm = -0.65
        leg = 0.20
    elseif speed > 0.1 then
        phase = (phase + step * math.min(speed * 0.75, 12)) % (2 * math.pi)
        local swing = math.sin(phase)
        arm = 0.85 * swing
        leg = -0.70 * swing
        if climbing then
            arm = arm - 0.65
        end
    else
        phase = 0
    end

    rightShoulder.DesiredAngle = arm
    -- Left and right motors have opposing axes.
    leftShoulder.DesiredAngle = (jumping or falling) and -arm or arm
    rightHip.DesiredAngle = leg
    leftHip.DesiredAngle = (jumping or falling) and -leg or leg
end)
