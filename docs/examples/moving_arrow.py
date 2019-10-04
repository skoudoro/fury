from fury import actor, window, utils
import numpy as np

centers = np.array([[0, 0, 0], [1, 0, 0], [2, 0, 0]])
dirs = np.array([[0, 1, 0], [1, 0, 0], [0, 0.5, 0.5]])

arrows = actor.arrow(centers=centers, colors=(1, 0, 0), directions=dirs)
showm = window.ShowManager(size=(800, 600))


def timer_callback(_obj, _event):
    nb_pts = arrows.GetMapper().GetInput().GetReferenceCount()
    pts = utils.numpy_support.vtk_to_numpy(arrows.GetMapper().GetInput().GetPoints().GetData())
    # centers = [np.mean(p, axis=0).astype(np.int) for p in np.split(pts, nb_pts)]
    # print(centers)

    # Per elements
    elements = np.split(pts, nb_pts)
    elements[0] += np.array([[0.01, 0, 0]])
    elements[1] -= np.array([[0.02, 0, 0]])
    elements[2] += np.array([[0.03, 0.03, 0]])
    pts = np.concatenate(elements)

    # print(pts)

    arrows.GetMapper().GetInput().SetPoints(utils.numpy_to_vtk_points(pts))
    arrows.GetMapper().GetInput().ComputeBounds()

    showm.render()


showm.scene.add(arrows)
showm.add_timer_callback(True, 200, timer_callback)

showm.start()
