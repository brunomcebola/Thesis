from mpl_toolkits.mplot3d import Axes3D
import matplotlib.pyplot as plt


fig = plt.figure()
ax = fig.add_subplot(111, projection='3d')

c=["red", "green", "blue"]
label=["x", "y", "z"]

s_x = [0, 0, 0]
s_y = [0, 0, 0]
s_z = [0, 0, 0]
e_x = [1, 0, 0]
e_y = [0, 1, 0]
e_z  =[0, 0, 1]

for i in range(0, 3):
    ax.plot([s_x[i], e_x[i]], [s_y[i],e_y[i]],zs=[s_z[i],e_z[i]], color=c[i])
    ax.text(e_x[i], e_y[i], e_z[i], label[i], None)

    
# Tweaking display region and labels
ax.set_xlim(-1.5, 1.5)
ax.set_ylim(-1.5, 1.5)
ax.set_zlim(-1.5, 1.5)

plt.show()