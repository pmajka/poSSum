The coarse-to-fine script splits a series of rigid transformation into low- and
high- frequency components. The overall idea of how this script works is
described toroughly in the paper by XXXX et. al. 2006. Although the actual
implementation is a bit different.


Biref description
=================

Created two series of rigid transformations out of a single series.

Implementation details
======================

Split transformation into parameters. Smooth parameters. Create a new series of transformations.

#TODO: provide tutorials and documentation.
Coarse to fine transformation merger.
Obligatory command line parameters:

    1. self.options.sliceIndex
    2. --fine-transform-filename-template
    3. --output-transform-filename-template
    4. --smooth-transform-filename-template


Implementation details
======================

:math:`n` -- number of images in the stack,

:math:`\mathbf{A}=(A_1, \ldots, A_n)` -- something,

:math:`\mathbf{B}=(B_1, \ldots, B_n)` -- something,

:math:`\mathbb{C}=\left(C_{(t^1_x,t^1_y,\theta^1)}, \ldots, C_{(t^n_x,t^n_y,\theta^n)}\right)` - series of coarse transformations,

:math:`\mathbb{F}=\left(F_{(t^1_x,t^1_y,\theta^1)}, \ldots, F_{(t^n_x,t^n_y,\theta^n)}\right)` - series of fine affine transformations,

:math:`\mathbb{M}=\left(M_{(t^1_x,t^1_y,\theta^1)}, \ldots, M_{(t^n_x,t^n_y,\theta^n)}\right)` - series of final affine transformations, beeing a result of merging coarse-to-fine.

Let the :

.. math::
   :nowrap:

   \begin{equation}
   \mathbb{F} \circ \mathbb{C} = \left( F_{(t^1_x,t^1_y,\theta^1)} \circ C_{(t^1_x,t^1_y,\theta^1), \ldots, } F_{(t^n_x,t^n_y,\theta^n)} \circ C_{(t^n_x,t^n_y,\theta^n)} \right).
   \end{equation}

xxxx :math:`T_{(t^1_x,t^1_y,\theta^1)}, \ldots, T_{(t^n_x,t^n_y,\theta^n)}` xxxxx.

.. math::
   :nowrap:

   \begin{equation}
   \label{form:gaussian_kernel}
   K(i,\sigma) = \frac{1}{\sqrt{2\pi}\cdot\sigma}\cdot e^{-\frac{i^2}{2\sigma^2}}.
   \end{equation}
   
xxxx


.. math::
   :nowrap:

    \begin{equation}
    \begin{split}
        \left( t'^1_x, \ldots, t'^n_x \right) &= \left( t^1_x, \ldots, t^n_x \right) \ast K_{\sigma_t}, \\
        \left( t'^1_y, \ldots, t'^n_y \right) &= \left( t^1_y, \ldots, t^n_y \right) \ast K_{\sigma_t}, \\
        \left( \theta'^1, \ldots, \theta'^n \right) &= \left( \theta^1, \ldots, \theta^n \right) \ast K_{\sigma_r}
    \end{split}
    \end{equation}

xxxx :math:`T_{\mu'_1}, \ldots, T_{\mu'_n} = T_{(t'^1_x, t'^1_y, \theta'^1)}, \ldots, T_{(t'^n_x, t'^n_y, \theta'^n)}`. 
xxxx(:math:`\sigma_r`) oraz przesunięciom (:math:`\sigma_t`).

.. math::
   :nowrap:

    \begin{equation}
    \underbrace{\mathbb{F} \ast K_{\sigma_r,\sigma_t}}_{\substack{\text{skladowa}\\\text{niskoczlstotliwosciowa}}}  \circ \mathbb{C}.
    \end{equation}

.. math::
   :nowrap:

    \begin{equation}
    \label{form:koncowa_transformacja_afiniczna}
    \mathbb{M} = \underbrace{ \left( \mathbb{F} \ast K_{\sigma_r,\sigma_t} \right )^{-1} \circ \mathbb{F}}_{\substack{\text{skladowa}\\\text{wysokoczestotliwosciowa}}} \circ \mathbb{C}.
    \end{equation}


dddd
