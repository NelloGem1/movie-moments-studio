"""Polished MagnatesMedia-style Manim scene: Howard Hughes (~3 min, 1080p)."""
from manim import *
import numpy as np

BG = "#0a0a0f"
FG = "#e8e8ec"
ACCENT = "#c0392b"
DIM = "#55556a"


def stick_figure(scale=1.0, color=FG):
    g = VGroup()
    head = Circle(radius=0.28 * scale, color=color, stroke_width=3).shift(UP * 1.7 * scale)
    body = Line(UP * 1.45 * scale, DOWN * 0.3 * scale, color=color, stroke_width=3)
    arm_l = Line(UP * 1.2 * scale + LEFT * 0.15 * scale,
                 UP * 0.7 * scale + LEFT * 0.55 * scale, color=color, stroke_width=3)
    arm_r = Line(UP * 1.2 * scale + RIGHT * 0.15 * scale,
                 UP * 0.7 * scale + RIGHT * 0.55 * scale, color=color, stroke_width=3)
    leg_l = Line(DOWN * 0.3 * scale + LEFT * 0.1 * scale,
                 DOWN * 1.3 * scale + LEFT * 0.35 * scale, color=color, stroke_width=3)
    leg_r = Line(DOWN * 0.3 * scale + RIGHT * 0.1 * scale,
                 DOWN * 1.3 * scale + RIGHT * 0.35 * scale, color=color, stroke_width=3)
    return VGroup(head, body, arm_l, arm_r, leg_l, leg_r)


def big_text(t, size=48, color=FG):
    return Text(t, font_size=size, color=color, font="Arial")


def fade_all(mobjects, run_time=1.2):
    return FadeOut(VGroup(*[m for m in mobjects if m is not None]), run_time=run_time)


class HughesStory(Scene):
    def construct(self):
        self.camera.background_color = BG

        # ---- 1. Intro title ----
        # subtle glow ring behind title
        ring = Circle(radius=2.2, color=DIM, stroke_width=1, stroke_opacity=0.4)
        title = big_text("HOWARD HUGHES", 72).shift(UP * 0.6)
        sub = big_text("1905 — 1976", 36, DIM).next_to(title, DOWN, buff=0.5)
        self.play(Create(ring), run_time=2)
        self.play(Write(title), FadeIn(sub, shift=UP * 0.3), run_time=3)
        self.play(ring.animate.set_stroke(opacity=0.15).scale(1.1), run_time=10)
        self.play(FadeOut(VGroup(ring, title, sub)), run_time=1.5)

        # ---- 2. Fortune + Hollywood ----
        fortune = big_text("BILLIONAIRE BY 18", 56).shift(UP * 1.2)
        self.play(Write(fortune), run_time=2.5)
        counter = Text("$0", font_size=64, color=ACCENT).move_to(DOWN * 0.4)
        target = Text("$400,000,000", font_size=52, color=ACCENT).move_to(DOWN * 0.4)
        self.play(FadeIn(counter), run_time=1)
        # count up through intermediate values
        for v in ["$10,000,000", "$100,000,000"]:
            tmp = Text(v, font_size=56, color=ACCENT).move_to(DOWN * 0.4)
            self.play(counter.animate.become(tmp), run_time=2.5)
        self.play(counter.animate.become(target), run_time=3)
        film = VGroup(*[Rectangle(width=0.4, height=0.25, color=DIM, fill_opacity=0.5,
                                  stroke_width=1).shift(LEFT * 2 + UP * i * 0.3) for i in range(3)])
        self.play(fortune.animate.shift(UP * 2.2), FadeIn(film, shift=RIGHT * 2), run_time=2)
        self.wait(9)
        self.play(fade_all([fortune, counter, film]), run_time=1.5)

        # ---- 3. Aviation: plane actually flies ----
        plane = Polygon(
            LEFT * 1.6, LEFT * 0.4 + UP * 0.4, RIGHT * 0.9 + UP * 0.4,
            RIGHT * 1.6, RIGHT * 0.4 + DOWN * 0.1, LEFT * 0.4 + DOWN * 0.1,
            color=FG, fill_opacity=0.15, stroke_width=2,
        ).shift(UP * 1.0)
        contrail = Line(plane.get_right(), plane.get_right() + LEFT * 4,
                        color=DIM, stroke_width=2, stroke_opacity=0.5)
        avi_label = big_text("AVIATION", 48).next_to(plane, DOWN, buff=2.0)
        self.play(FadeIn(VGroup(plane, contrail), shift=LEFT * 4), Write(avi_label), run_time=3)
        # plane flies across and exits
        self.play(VGroup(plane, contrail).animate.shift(RIGHT * 14).set_opacity(0),
                  run_time=6, rate_func=linear)
        record = big_text("WORLD RECORDS", 36, ACCENT).next_to(avi_label, DOWN, buff=0.6)
        self.play(Write(record), run_time=2.5)
        self.wait(7)
        self.play(fade_all([avi_label, record]), run_time=1.5)

        # ---- 4. OCD: trembling figure + germs ----
        fig = stick_figure(1.4).shift(DOWN * 0.8)
        germs = VGroup(*[Dot(ORIGIN, radius=0.12, color=ACCENT) for _ in range(14)])
        germs.arrange_in_grid(rows=2, buff=0.4).shift(UP * 2)
        self.play(FadeIn(fig), run_time=1.5)
        # trembling updater
        t0 = [0.0]
        def tremble(mob, dt):
            t0[0] += dt
            mob.shift(RIGHT * 0.008 * np.sin(t0[0] * 18) + UP * 0.004 * np.sin(t0[0] * 23))
        fig.add_updater(tremble)
        self.play(LaggedStart(*[FadeIn(g, scale=0.5) for g in germs], lag_ratio=0.08), run_time=3)
        warn = big_text("OCD. ANXIETY. FEAR.", 40, ACCENT).next_to(fig, UP, buff=2.2)
        self.play(Write(warn), run_time=2.5)
        self.wait(7)
        fig.remove_updater(tremble)
        self.play(fade_all([fig, germs, warn]), run_time=1.5)

        # ---- 5. Desert Inn ----
        hotel = VGroup()
        for i in range(6):
            hotel.add(Rectangle(width=0.5, height=3.5, color=DIM, fill_opacity=0.3,
                                stroke_width=1).shift(LEFT * 2.2 + i * 0.85))
        hotel.shift(DOWN * 0.2)
        door = Rectangle(width=0.7, height=1.4, color=FG, fill_opacity=0.1).next_to(hotel, DOWN, buff=-0.3)
        hlabel = big_text("DESERT INN — LAS VEGAS", 38).next_to(hotel, UP, buff=0.5)
        self.play(LaggedStart(*[Create(r) for r in hotel], lag_ratio=0.1), Write(hlabel), run_time=3)
        never = big_text("NEVER LEFT", 48, ACCENT).next_to(door, DOWN, buff=0.4)
        self.play(Write(never), run_time=2)
        # windows flicker on
        wins = VGroup(*[Rectangle(width=0.18, height=0.3, color=ACCENT, fill_opacity=0.6, stroke_width=0)
                        for i in range(8)])
        for i, w in enumerate(wins):
            w.move_to(hotel[i // 2].get_center() + UP * (0.9 - (i % 4) * 0.55) + LEFT * 0.1 * (i % 2))
        self.play(LaggedStart(*[FadeIn(w, scale=0.3) for w in wins], lag_ratio=0.2), run_time=3)
        self.wait(7)
        self.play(fade_all([hotel, hlabel, door, never, wins]), run_time=1.5)

        # ---- 6. 13 years inside: calendar + TV glow ----
        cal = Rectangle(width=2.2, height=2.8, color=DIM, fill_opacity=0.3, stroke_width=2).shift(LEFT * 1.8)
        cal_title = big_text("1966", 40, ACCENT).next_to(cal, UP, buff=0.3)
        # flipping pages
        pages = VGroup()
        for i in range(4):
            p = Rectangle(width=2.0, height=2.5, color=FG, fill_opacity=0.08,
                          stroke_width=1).move_to(cal.get_center())
            pages.add(p)
        self.play(Create(cal), Write(cal_title), run_time=2)
        for p in pages:
            self.play(p.animate.rotate(PI / 2, axis=OUT).shift(UP * 0.3).set_opacity(0), run_time=0.8)
        years = big_text("13 YEARS INSIDE", 44, ACCENT).shift(RIGHT * 1.6)
        tv = Rectangle(width=1.6, height=0.9, color=ACCENT, fill_opacity=0.25).shift(RIGHT * 1.6 + DOWN * 1.4)
        glow = SurroundingRectangle(tv, color=ACCENT, buff=0.15, stroke_opacity=0.4)
        self.play(Write(years), FadeIn(VGroup(tv, glow)), run_time=2.5)
        note = Text("notes slid under the door", font_size=24, color=DIM).next_to(tv, DOWN, buff=0.5)
        self.play(FadeIn(note), run_time=2)
        self.wait(7)
        self.play(fade_all([cal, cal_title, years, tv, glow, note]), run_time=1.5)

        # ---- 7. Death ----
        chair = VGroup(Circle(radius=0.3).shift(UP * 1.1),
                       Line(UP * 0.8, DOWN * 0.2),
                       Line(DOWN * 0.2, DOWN * 1.1 + LEFT * 0.3),
                       Line(DOWN * 0.2, DOWN * 1.1 + RIGHT * 0.3))
        chair.set_color(FG).set_stroke(width=3)
        iv = Line(UP * 2, DOWN * 0.2, color=ACCENT, stroke_width=2).next_to(chair, RIGHT, buff=0.3)
        drip = Dot(UP * 2 + RIGHT * 0.15, radius=0.08, color=ACCENT)
        spot = Circle(radius=1.6, color=FG, stroke_width=1, stroke_opacity=0.25).move_to(chair)
        self.play(FadeIn(chair), Create(iv), FadeIn(drip), FadeIn(spot), run_time=2.5)
        date = big_text("APRIL 5, 1976", 44, ACCENT).next_to(chair, DOWN, buff=0.8)
        self.play(Write(date), run_time=2)
        self.wait(9)
        self.play(fade_all([chair, iv, drip, spot, date]), run_time=1.8)

        # ---- 8. Estate battle ----
        money = big_text("$2 BILLION+", 52).shift(UP * 1)
        self.play(Write(money), run_time=2.5)
        papers2 = VGroup(*[Text("WILL?", font_size=30, color=DIM).shift(LEFT * 1.2 + i * 1.2 + DOWN * (0.4 * (i % 2)))
                           for i in range(5)])
        self.play(LaggedStart(*[FadeIn(p, shift=UP * 0.5) for p in papers2], lag_ratio=0.15), run_time=3)
        gavel = big_text("LEGAL BATTLE", 36, ACCENT).next_to(money, DOWN, buff=0.8)
        self.play(Write(gavel), run_time=2)
        self.wait(7)
        self.play(fade_all([money, papers2, gavel]), run_time=1.5)

        # ---- 9. Legacy + outro ----
        lesson = VGroup(
            big_text("GENIUS?", 40).shift(UP * 2),
            big_text("WEALTH?", 40).shift(UP * 1),
            big_text("PEACE OF MIND?", 40, ACCENT).shift(UP * 0),
        )
        self.play(LaggedStart(*[FadeIn(t, shift=RIGHT * 0.5) for t in lesson], lag_ratio=0.3), run_time=3)
        self.wait(8)
        self.play(FadeOut(lesson), run_time=1.5)
        final = big_text("HOWARD HUGHES", 64).shift(UP * 0.5)
        final_sub = big_text("This is Howard Hughes.", 32, DIM).next_to(final, DOWN, buff=0.5)
        self.play(Write(final), FadeIn(final_sub), run_time=3)
        self.wait(23)
