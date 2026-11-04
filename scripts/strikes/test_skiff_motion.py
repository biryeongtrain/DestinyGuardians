import unittest
import copy
import json
import numpy as np
from retarget_skiff_motion import continuous_euler, euler_matrix, skin_delta, retarget


class SkiffMotionTest(unittest.TestCase):
    def test_world_skin_delta_is_independent_of_imported_bone_roll(self):
        rest=np.eye(4);rest[:3,:3]=euler_matrix(np.array([[.6,-.9,1.2]]))[0];rest[:3,3]=[3,4,5]
        delta=np.eye(4);delta[:3,:3]=euler_matrix(np.array([[-.2,.7,.9]]))[0];delta[:3,3]=[1,2,3]
        np.testing.assert_allclose(skin_delta(rest,np.array([delta@rest]))[0],delta,atol=1e-12)

    def test_nonrigid_source_motion_is_not_silently_discarded(self):
        scale=np.eye(4);scale[0,0]=1.1
        with self.assertRaisesRegex(ValueError,'Nonrigid'):skin_delta(np.eye(4),np.array([scale]))

    def test_continuity_across_pi_and_gimbal_branch(self):
        angles=np.column_stack([np.linspace(2.9,3.4,61),np.linspace(1.4,1.8,61),np.linspace(.2,.6,61)])
        rotations=euler_matrix(angles);converted=continuous_euler(rotations)
        np.testing.assert_allclose(euler_matrix(converted),rotations,atol=1e-10)
        self.assertLess(np.max(np.abs(np.diff(converted,axis=0))),.1)

    def fixture(self):
        rest=np.repeat(np.eye(4)[None],3,axis=0);rest[:,0,3]=[0,1,2]
        drive=dict(names=np.array(['root','child','extra']),parents=np.array(['','root','child']),rest=rest)
        native=dict(names=np.array(['R','C']),rest=rest[:2],clip_test=rest[None,:2],
                    metadata=json.dumps(dict(source='fixture',sha256='fixture',clips=[dict(tag='test',manifestFrames=81)])))
        extra=dict(name='extra',uuid='extra',origin=[32,0,0],children=[])
        child=dict(name='child',uuid='child',origin=[16,0,0],children=[extra])
        model=dict(outliner=[dict(name='root',uuid='root',origin=[0,0,0],children=[child])],animations=[],devils_lair={})
        mapping=dict(matched=[dict(driveBone='root',nativeBone='R',driveParent=None),
                              dict(driveBone='child',nativeBone='C',driveParent='root')])
        return model,drive,native,mapping

    def test_preserves_auxiliary_hierarchy_and_source_hold_duration(self):
        args=self.fixture();before=copy.deepcopy(args[0]);result,report=retarget(*args)
        self.assertEqual(args[0],before)
        self.assertEqual(result['outliner'],before['outliner'])
        animation=result['animations'][0]
        self.assertAlmostEqual(animation['length'],80/30,places=6)
        self.assertNotIn('extra',animation['animators'])
        self.assertEqual(report['additionalBones']['extra']['mappedAncestor'],'child')
        self.assertTrue(report['clips'][0]['constantHold'])

    def test_changed_auxiliary_hierarchy_is_rejected(self):
        args=self.fixture();args[1]['parents'][2]='root'
        with self.assertRaisesRegex(ValueError,'hierarchy'):retarget(*args)


if __name__=='__main__':unittest.main()
