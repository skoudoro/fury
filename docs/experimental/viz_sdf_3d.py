"""
DISPLAY -             x-y pixel values in a window
NORMALIZED DISPLAY -  x-y (0,1) normalized values
VIEWPORT -            x-y pixel values in viewport
NORMALIZED VIEWPORT - x-y (0,1) normalized value in viewport
PROJECTION -          View coordinates transformed by the ortho/perspective
                      equations and normalized to -1,1 cube on X and Y. The
                      z range is defined by the code and may be -1,1
                      for OpenGL or other values. This is the coordinate system
                      that is typically coming out of the vertex shader.
VIEW -                x-y-z values in camera coordinates. The origin is
                      at the camera position and the orientation is such
                      that the -Z axis is the view direction, the X axis
                      is the view right, and Y axis is view up. This is
                      a translation and rotation from world coordinates
                      based on the camera settings.
WORLD -               x-y-z global coordinate values
MODEL -               The coordinate system specific to a dataaet or
                      actor. This is normally converted into WORLD coordinates
                      as part of the rendering process.

"""
from fury import actor, window, primitive as fp, utils
import numpy as np
from vtk.util import numpy_support
import vtk


def apply_sdf(act):

    mapper = act.GetMapper()
    mapper.MapDataArrayToVertexAttribute(
        "center", "center", vtk.vtkDataObject.FIELD_ASSOCIATION_POINTS, -1)

    mapper.AddShaderReplacement(
        vtk.vtkShader.Vertex,
        "//VTK::ValuePass::Dec",
        True,
        """
        //VTK::ValuePass::Dec
        in vec3 center;
        out vec3 centeredVertexMC;
        """,
        False
    )

    mapper.AddShaderReplacement(
        vtk.vtkShader.Vertex,
        "//VTK::ValuePass::Impl",
        True,
        """
        //VTK::ValuePass::Impl
        centeredVertexMC = vertexMC.xyz - center;
        vec3 scalingFactor = 1. / abs(centeredVertexMC.xyz);
        centeredVertexMC *= scalingFactor;

        """,
        False
    )

    mapper.AddShaderReplacement(
        vtk.vtkShader.Fragment,
        "//VTK::ValuePass::Dec",
        True,
        """
        //VTK::ValuePass::Dec
        in vec3 centeredVertexMC;

        uniform mat4 MCDCMatrix;
        uniform mat4 MCVCMatrix;
        uniform mat4 WCMCMatrix; // - world to model
        uniform mat4 MCWCMatrix; // - model to world
        uniform mat4 MCPCMatrix; // - model to projection
        uniform mat4 WCVCMatrix; // - world to view - half of the camera transform
        uniform mat4 WCPCMatrix; // - world to projection
        uniform mat4 VCPCMatrix; // - view to projection - the other part of the camera transform


        float sdRoundBox( vec3 p, vec3 b, float r )
        {
            vec3 q = abs(p) - b;
            return length(max(q,0.0)) + min(max(q.x,max(q.y,q.z)),0.0) - r;
        }

        float sdEllipsoid( vec3 p, vec3 r )
        {
        float k0 = length(p/r);
        float k1 = length(p/(r*r));
        return k0*(k0-1.0)/k1;
        }
        float sdCylinder(vec3 p, float h, float r)
        {
            vec2 d = abs(vec2(length(p.xz),p.y)) - vec2(h,r);
            return min(max(d.x,d.y),0.0) + length(max(d,0.0));
        }
        float sdSphere(vec3 pos, float r)
        {
            float d = length(pos) - r;

            return d;
        }

        float map( in vec3 pos)
        {
            float d = sdSphere(pos, 0.9);
            float d1 = sdCylinder(pos, 0.5, 0.9);
            float d2 = sdEllipsoid(pos, vec3(0.4, 0.6, 0.9));
            float d3 = sdRoundBox(pos, vec3(0.2, 0.3, 0.4), 0.05);

            //.xy
            //return min(min(min(d, d1), d2), d3);
            return d1;
        }

        vec3 calcNormal( in vec3 pos )
        {
            vec2 e = vec2(0.0001,0.0);
            return normalize( vec3(map(pos + e.xyy) - map(pos - e.xyy ),
                                   map(pos + e.yxy) - map(pos - e.yxy),
                                   map(pos + e.yyx) - map(pos - e.yyx)
                                   )
                            );
        }

        float castRay(in vec3 ro, vec3 rd)
        {
            float t = 0.0;
            for(int i=0; i < 300; i++)
            {
                vec3 pos = ro + t * rd;
                vec3 nor = calcNormal(pos);

                float h = map(pos);
                if (h < 0.001) break;

                t += h;
                if (t > 20.0) break;
            }
            return t;
        }
        """,
        False
    )

    mapper.AddShaderReplacement(
        vtk.vtkShader.Fragment,
        "//VTK::Light::Impl",
        True,
        """
        // Renaming variables passed from the Vertex Shader
        vec3 color = vertexColorVSOutput.rgb;
        vec3 point = centeredVertexMC;
        //fragOutput0 = vec4(centeredVertexMC, 0.7);



        vec3 uu = vec3(MCVCMatrix[0][0], MCVCMatrix[1][0], MCVCMatrix[2][0]); // camera right
        vec3 vv = vec3(MCVCMatrix[0][1], MCVCMatrix[1][1], MCVCMatrix[2][1]); //  camera up
        vec3 ww = vec3(MCVCMatrix[0][2], MCVCMatrix[1][2], MCVCMatrix[2][2]); // camera direction
        //vec3 ro = -MCVCMatrix[3].xyz * mat3(MCVCMatrix);  // camera position in world space
        vec4 ro = -MCVCMatrix[3] * MCVCMatrix;  // camera position in world space

        mat4 MCVCMatrixInverse = inverse(MCVCMatrix);
        //ro = MCVCMatrixInverse * vec4(ro.xyz, 1.);
        //ro = MCVCMatrixInverse * ro;
        //vec4 tmp = vec4(point, 1) * MCVCMatrix;
        //point = tmp.xyz;

        // create view ray
        vec3 rd = normalize(point - ro.xyz);
        vec3 col = vec3(1, 0, 0);

        //fragOutput0 = normalize(ro);
        //fragOutput0 = vec4(ro.xyz, 1);

        float t = castRay(ro.xyz, rd);
        if (t < 20.0)
        {
            vec3 pos = ro.xyz + t * rd;
            vec3 nor = calcNormal(pos);
            fragOutput0 = vec4(nor, 1.0);
        }
        else{
            //fragOutput0 = vec4(0,1,0, 1.0);
            discard;
            }


        /*float len = length(point);
        // VTK Fake Spheres
        float radius = 1.;
        if(len > radius)
          discard;
        vec3 normalizedPoint = normalize(vec3(point.xy, sqrt(1. - len)));
        vec3 direction = normalize(vec3(1., 1., 1.));
        float df = max(0, dot(direction, normalizedPoint));
        float sf = pow(df, 24);
        fragOutput0 = vec4(max(df * color, sf * vec3(1)), 1);*/
        """,
        False
    )


def test_sdf_3d():
    scene = window.Scene()
    scene.background((0.8, 0.8, 0.8))

    centers = np.array([[2, 0, 0], [0, 0, 0], [-2, 0, 0]])
    # np.random.rand(3, 3) * 3
    # colors = np.array([[255, 0, 0], [0, 255, 0], [0, 0, 255]])
    colors = np.random.rand(3, 3) * 255
    scale = 1  # np.random.rand(3) * 5

    # Set up primitive
    verts, faces = fp.prim_box()
    res = fp.repeat_primitive(verts, faces, centers=centers, colors=colors,
                              scale=scale)

    big_verts, big_faces, big_colors, big_centers = res

    act = utils.get_actor_from_primitive(big_verts, big_faces, big_colors)
    # actor.GetProperty().BackfaceCullingOff()
    vtk_centers = numpy_support.numpy_to_vtk(big_centers, deep=True)
    vtk_centers.SetNumberOfComponents(3)
    vtk_centers.SetName("center")
    act.GetMapper().GetInput().GetPointData().AddArray(vtk_centers)

    apply_sdf(act)

    scene.add(act)
    scene.add(actor.axes())
    window.show(scene, size=(1960, 1200))


if __name__ == "__main__":
    test_sdf_3d()