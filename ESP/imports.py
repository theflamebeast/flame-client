from system.pyj.minescript import *;

# MC
try:
  resource_location = JavaClass("net.minecraft.resources.ResourceLocation")
except:
  try:
    resource_location = JavaClass("net.minecraft.util.ResourceLocation")
  except:
    resource_location = JavaClass("net.minecraft.class_2960")

try:
  style = JavaClass("net.minecraft.network.chat.Style")
except:
  style = JavaClass("net.minecraft.class_2583")

try:
  component = JavaClass("net.minecraft.network.chat.Component")
except:
  component = JavaClass("net.minecraft.class_2561")

try:
  minecraft_class = JavaClass("net.minecraft.client.Minecraft")
except:
  minecraft_class = JavaClass("net.minecraft.class_310")

try:
  argb = JavaClass("net.minecraft.util.ARGB")
except:
  try:
    argb = JavaClass("net.minecraft.class_5428")
  except:
    try:
      # Fallback for older versions (1.21.1 and below) where it was FastColor.ARGB32
      argb = JavaClass("net.minecraft.util.FastColor$ARGB32")
    except:
      try:
        argb = JavaClass("net.minecraft.class_3532$class_3533")
      except:
         # Last resort: FastColor
         try:
            argb = JavaClass("net.minecraft.util.FastColor")
         except:
            argb = JavaClass("net.minecraft.class_3532")

try:
  vector3 = JavaClass("net.minecraft.world.phys.Vec3")
except:
  vector3 = JavaClass("net.minecraft.class_243")

try:
  vector2 = JavaClass("net.minecraft.world.phys.Vec2")
except:
  vector2 = JavaClass("net.minecraft.class_241")

# JAVA
j_float = JavaClass("java.lang.Float");
j_integer = JavaClass("java.lang.Integer");
j_math = JavaClass("java.lang.Math");

# FABRIC
hud_render_callback = JavaClass("net.fabricmc.fabric.api.client.rendering.v1.HudRenderCallback");
