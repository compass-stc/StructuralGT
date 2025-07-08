from ovito.data import DataCollection
from ovito.vis import Viewport
from ovito.io import import_file
from ovito.modifiers import AffineTransformationModifier
from ovito.pipeline import ModifierInterface
from traits.api import Range, observe
import numpy as np
import math

class TurntableAnimation(ModifierInterface):
    # From https://www.ovito.org/manual/python/modules/ovito_pipeline.html#ovito.pipeline.ModifierInterface

    # Parameter controlling the animation length (value can be changed by the user):
    duration = Range(low=1, value=100)

    def compute_trajectory_length(self, **kwargs):
        return self.duration

    def modify(self, data: DataCollection, *, frame: int, **kwargs):
        # Apply a rotational transformation to the whole dataset with a time-dependent angle of rotation:
        theta = np.deg2rad(frame * 360 / self.duration)
        tm = [[np.cos(theta), -np.sin(theta), 0, 0],
                [np.sin(theta),  np.cos(theta), 0, 0],
                [            0,              0, 1, 0]]
        data.apply(AffineTransformationModifier(transformation=tm))

    # This is needed to notify the pipeline system whenever the animation length is changed by the user:
    @observe("duration")
    def anim_duration_changed(self, event):
        self.notify_trajectory_length_changed()


def write_turntable(fname):
    pipeline = import_file(fname)
    data = pipeline.compute()
    T = TurntableAnimation()
    T.modify(data, frame=0)
    pipeline.modifiers.append(T)
    pipeline.add_to_scene()

    vp = Viewport()
    vp.type = Viewport.Type.Perspective
    vp.camera_dir = (1.0, -0.0, -0.0)
    vp.zoom_all()

    vp.render_anim(filename="_myimage.mp4", )
