"""Avatar 'I see you' moment — original animated short (no trailer footage)."""
from manim import *


class ISeeYou(Scene):
    def construct(self):
        # deep Pandora night
        self.camera.background_color = "#050810"

        # floating bioluminescent spores
        spores = VGroup()
        import random
        rng = random.Random(3)
        for _ in range(60):
            dot = Dot(radius=rng.uniform(0.01, 0.04),
                      color=ManimColor("#00FFCC").interpolate(
                          ManimColor("#8844FF"), rng.random()),
                      fill_opacity=rng.uniform(0.2, 0.7))
            dot.move_to([rng.uniform(-8, 8), rng.uniform(-4.5, 4.5), 0])
            spores.add(dot)
        self.play(FadeIn(spores, lag_ratio=0.05), run_time=3)

        # distant floating mountains silhouettes
        mountains = VGroup()
        for i, (x, h) in enumerate([(-6, 2.2), (-3, 3.4), (0, 2.8), (3.5, 3.0), (6.5, 2.4)]):
            peak = Polygon([x-1.4,-4.5,0], [x,-4.5+h,0], [x+1.4,-4.5,0],
                           fill_color="#0A1420", fill_opacity=0.9,
                           stroke_color="#00FFCC", stroke_opacity=0.15, stroke_width=1)
            mountains.add(peak)
        self.play(LaggedStart(*[FadeIn(m, shift=UP * 0.3) for m in mountains],
                              lag_ratio=0.15), run_time=2.5)

        # moon rises
        moon = Circle(radius=1.1, color="#DDEEFF", fill_opacity=0.9,
                      fill_color="#DDEEFF", stroke_width=0)
        moon.move_to([5.5, -1.0, 0])
        moon_glow = Circle(radius=1.6, color="#88AAFF", stroke_width=0,
                           fill_opacity=0.12, fill_color="#88AAFF")
        moon_glow.move_to(moon.get_center())
        self.play(FadeIn(moon_glow), FadeIn(moon), run_time=3)
        self.play(moon.animate.shift(UP * 1.5), moon_glow.animate.shift(UP * 1.5),
                  run_time=4)

        # Jake silhouette (human) — walks in from left
        jake = VGroup()
        body = Polygon([0,0,0], [0.25,1.5,0], [0.55,1.5,0], [0.8,0,0],
                       fill_color="#0D1520", fill_opacity=1, stroke_width=0)
        head = Circle(radius=0.28, color="#0D1520", fill_opacity=1,
                      fill_color="#0D1520", stroke_width=0)
        head.move_to(body.get_top() + UP * 0.35)
        jake.add(body, head)
        jake.scale(1.6).move_to([-3.2, -2.2, 0])

        # Neytiri silhouette (Na'vi) — from right, ears + tail hint
        ney = VGroup()
        nbody = Polygon([0,0,0], [0.25,1.5,0], [0.55,1.5,0], [0.8,0,0],
                        fill_color="#081410", fill_opacity=1, stroke_width=0)
        nhead = Circle(radius=0.30, color="#081410", fill_opacity=1,
                       fill_color="#081410", stroke_width=0)
        nhead.move_to(nbody.get_top() + UP * 0.4)
        ear1 = Polygon([-0.5,0.2,0], [-0.85,0.85,0], [-0.35,0.45,0],
                       fill_color="#081410", fill_opacity=1, stroke_width=0)
        ear2 = Polygon([0.5,0.2,0], [0.85,0.85,0], [0.35,0.45,0],
                       fill_color="#081410", fill_opacity=1, stroke_width=0)
        ear1.move_to(nhead.get_center() + LEFT * 0.15 + UP * 0.05)
        ear2.move_to(nhead.get_center() + RIGHT * 0.15 + UP * 0.05)
        tail = Line([0.8,0.3,0], [1.6,-0.4,0], color="#081410",
                    stroke_width=6)
        ney.add(nbody, nhead, ear1, ear2, tail)
        ney.scale(1.7).move_to([3.2, -2.2, 0])

        # rim light on figures
        rim_j = Line(jake[1].get_top() + LEFT * 0.2,
                     jake[1].get_top() + RIGHT * 0.2,
                     color="#00FFCC", stroke_width=2, stroke_opacity=0.7)
        rim_n = Line(ney[1].get_top() + LEFT * 0.2,
                     ney[1].get_top() + RIGHT * 0.2,
                     color="#00FFCC", stroke_width=2, stroke_opacity=0.7)

        self.play(FadeIn(jake), FadeIn(ney), run_time=2)
        self.play(Create(rim_j), Create(rim_n), run_time=1)

        # they turn toward each other, walk slowly together
        self.play(jake.animate.shift(RIGHT * 0.7),
                  ney.animate.shift(LEFT * 0.9), run_time=5)

        # spores drift toward them — one fluid motion, not 20s of singles
        drift_targets = VGroup(*[s.copy() for s in spores[::6]])
        for s in drift_targets:
            s.move_to(s.get_center() * 0.75 + ney.get_center() * 0.25)
        self.play(Transform(VGroup(*spores[::6]), drift_targets), run_time=3)

        # THE MOMENT — hold, spores brighten
        self.play(spores.animate.set_fill(opacity=0.9), run_time=1.5)

        # text: I SEE YOU
        text = Text("I  SEE  YOU", font_size=90, weight=BOLD,
                    color="#E8FFFF")
        text.set_stroke("#00FFCC", width=2, background=True)
        self.play(Write(text), run_time=2)
        self.wait(2.5)

        # fade spores, keep silhouettes + text
        self.play(spores.animate.set_fill(opacity=0.3),
                  FadeOut(mountains), FadeOut(moon), FadeOut(moon_glow),
                  run_time=2)
        self.wait(1)
        self.play(FadeOut(text), FadeOut(jake), FadeOut(ney),
                  FadeOut(rim_j), FadeOut(rim_n), run_time=2)
