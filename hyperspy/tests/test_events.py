import nose.tools as nt
import hyperspy.events as he


class EventsBase():
    def on_trigger(self, *args, **kwargs):
        self.triggered = True

    def on_trigger2(self, *args, **kwargs):
        self.triggered2 = True

    def trigger_check(self, trigger, should_trigger, *args):
        self.triggered = False
        trigger(*args)
        nt.assert_equal(self.triggered, should_trigger)

    def trigger_check2(self, trigger, should_trigger, *args):
        self.triggered2 = False
        trigger(*args)
        nt.assert_equal(self.triggered2, should_trigger)


class TestEventsSuppression(EventsBase):

    def setUp(self):
        self.events = he.Events()

        self.events.a = he.Event()
        self.events.b = he.Event()
        self.events.c = he.Event()

        self.events.a.connect(self.on_trigger)
        self.events.a.connect(self.on_trigger2)
        self.events.b.connect(self.on_trigger)
        self.events.c.connect(self.on_trigger)

    def test_simple_suppression(self):
        with self.events.a.suppress():
            self.trigger_check(self.events.a.trigger, False)
            self.trigger_check(self.events.b.trigger, True)

        with self.events.suppress():
            self.trigger_check(self.events.a.trigger, False)
            self.trigger_check(self.events.b.trigger, False)
            self.trigger_check(self.events.c.trigger, False)

        self.trigger_check(self.events.a.trigger, True)
        self.trigger_check(self.events.b.trigger, True)
        self.trigger_check(self.events.c.trigger, True)

    def test_suppression_restore(self):
        with self.events.a.suppress():
            with self.events.suppress():
                self.trigger_check(self.events.a.trigger, False)
                self.trigger_check(self.events.b.trigger, False)
                self.trigger_check(self.events.c.trigger, False)

            self.trigger_check(self.events.a.trigger, False)
            self.trigger_check(self.events.b.trigger, True)
            self.trigger_check(self.events.c.trigger, True)

    def test_suppresion_nesting(self):
        with self.events.a.suppress():
            with self.events.suppress():
                self.events.c._suppress = False
                self.trigger_check(self.events.a.trigger, False)
                self.trigger_check(self.events.b.trigger, False)
                self.trigger_check(self.events.c.trigger, True)

                with self.events.suppress():
                    self.trigger_check(self.events.a.trigger, False)
                    self.trigger_check(self.events.b.trigger, False)
                    self.trigger_check(self.events.c.trigger, False)

                self.trigger_check(self.events.a.trigger, False)
                self.trigger_check(self.events.b.trigger, False)
                self.trigger_check(self.events.c.trigger, True)

            self.trigger_check(self.events.a.trigger, False)
            self.trigger_check(self.events.b.trigger, True)
            self.trigger_check(self.events.c.trigger, True)

    def test_suppression_single(self):
        with self.events.b.suppress():
            with self.events.a.suppress_callback(self.on_trigger):
                self.trigger_check(self.events.a.trigger, False)
                self.trigger_check2(self.events.a.trigger, True)
                self.trigger_check(self.events.b.trigger, False)
                self.trigger_check(self.events.c.trigger, True)

            self.trigger_check(self.events.a.trigger, True)
            self.trigger_check2(self.events.a.trigger, True)
            self.trigger_check(self.events.b.trigger, False)
            self.trigger_check(self.events.c.trigger, True)

        # Reverse order:
        with self.events.a.suppress_callback(self.on_trigger):
            with self.events.b.suppress():
                self.trigger_check(self.events.a.trigger, False)
                self.trigger_check2(self.events.a.trigger, True)
                self.trigger_check(self.events.b.trigger, False)
                self.trigger_check(self.events.c.trigger, True)

            self.trigger_check(self.events.a.trigger, False)
            self.trigger_check2(self.events.a.trigger, True)
            self.trigger_check(self.events.b.trigger, True)
            self.trigger_check(self.events.c.trigger, True)

    @nt.raises(ValueError)
    def test_exception_event(self):
        try:
            with self.events.a.suppress():
                self.trigger_check(self.events.a.trigger, False)
                self.trigger_check(self.events.b.trigger, True)
                self.trigger_check(self.events.c.trigger, True)
                raise ValueError()
        finally:
            self.trigger_check(self.events.a.trigger, True)
            self.trigger_check(self.events.b.trigger, True)
            self.trigger_check(self.events.c.trigger, True)

    @nt.raises(ValueError)
    def test_exception_events(self):
        try:
            with self.events.suppress():
                self.trigger_check(self.events.a.trigger, False)
                self.trigger_check(self.events.b.trigger, False)
                self.trigger_check(self.events.c.trigger, False)
                raise ValueError()
        finally:
            self.trigger_check(self.events.a.trigger, True)
            self.trigger_check(self.events.b.trigger, True)
            self.trigger_check(self.events.c.trigger, True)

    @nt.raises(ValueError)
    def test_exception_single(self):
        try:
            with self.events.a.suppress_callback(self.on_trigger):
                self.trigger_check(self.events.a.trigger, False)
                self.trigger_check2(self.events.a.trigger, True)
                self.trigger_check(self.events.b.trigger, True)
                self.trigger_check(self.events.c.trigger, True)
                raise ValueError()
        finally:
            self.trigger_check(self.events.a.trigger, True)
            self.trigger_check2(self.events.a.trigger, True)
            self.trigger_check(self.events.b.trigger, True)
            self.trigger_check(self.events.c.trigger, True)

    @nt.raises(ValueError)
    def test_exception_nested(self):
        try:
            with self.events.a.suppress_callback(self.on_trigger):
                try:
                    with self.events.a.suppress():
                        try:
                            with self.events.suppress():
                                self.trigger_check(self.events.a.trigger,
                                                   False)
                                self.trigger_check2(self.events.a.trigger,
                                                    False)
                                self.trigger_check(self.events.b.trigger,
                                                   False)
                                self.trigger_check(self.events.c.trigger,
                                                   False)
                                raise ValueError()
                        finally:
                            self.trigger_check(self.events.a.trigger, False)
                            self.trigger_check2(self.events.a.trigger, False)
                            self.trigger_check(self.events.b.trigger, True)
                            self.trigger_check(self.events.c.trigger, True)
                finally:
                    self.trigger_check(self.events.a.trigger, False)
                    self.trigger_check2(self.events.a.trigger, True)
                    self.trigger_check(self.events.b.trigger, True)
                    self.trigger_check(self.events.c.trigger, True)
        finally:
            self.trigger_check(self.events.a.trigger, True)
            self.trigger_check2(self.events.a.trigger, True)
            self.trigger_check(self.events.b.trigger, True)
            self.trigger_check(self.events.c.trigger, True)

    def test_suppress_wrong(self):
        with self.events.a.suppress_callback(f_a):
            self.trigger_check(self.events.a.trigger, True)
            self.trigger_check2(self.events.a.trigger, True)

    def test_suppressor_init_args(self):
        with self.events.b.suppress():
            es = he.EventSupressor((self.events.a, self.on_trigger),
                                   self.events.c)
            with es.suppress():
                self.trigger_check(self.events.a.trigger, False)
                self.trigger_check2(self.events.a.trigger, True)
                self.trigger_check(self.events.b.trigger, False)
                self.trigger_check(self.events.c.trigger, False)
                with self.events.a.suppress_callback(self.on_trigger2):
                    self.trigger_check2(self.events.a.trigger, False)
                self.trigger_check2(self.events.a.trigger, True)

            self.trigger_check(self.events.a.trigger, True)
            self.trigger_check2(self.events.a.trigger, True)
            self.trigger_check(self.events.b.trigger, False)
            self.trigger_check(self.events.c.trigger, True)

        self.trigger_check(self.events.a.trigger, True)
        self.trigger_check2(self.events.a.trigger, True)
        self.trigger_check(self.events.b.trigger, True)
        self.trigger_check(self.events.c.trigger, True)

    def test_suppressor_add_args(self):
        with self.events.b.suppress():
            es = he.EventSupressor()
            es.add((self.events.a, self.on_trigger), self.events.c)
            with es.suppress():
                self.trigger_check(self.events.a.trigger, False)
                self.trigger_check2(self.events.a.trigger, True)
                self.trigger_check(self.events.b.trigger, False)
                self.trigger_check(self.events.c.trigger, False)
                with self.events.a.suppress_callback(self.on_trigger2):
                    self.trigger_check2(self.events.a.trigger, False)
                self.trigger_check2(self.events.a.trigger, True)

            self.trigger_check(self.events.a.trigger, True)
            self.trigger_check2(self.events.a.trigger, True)
            self.trigger_check(self.events.b.trigger, False)
            self.trigger_check(self.events.c.trigger, True)

        self.trigger_check(self.events.a.trigger, True)
        self.trigger_check2(self.events.a.trigger, True)
        self.trigger_check(self.events.b.trigger, True)
        self.trigger_check(self.events.c.trigger, True)

    def test_suppressor_all_callback_in_events(self):
        with self.events.b.suppress():
            es = he.EventSupressor()
            es.add((self.events, self.on_trigger),)
            with es.suppress():
                self.trigger_check(self.events.a.trigger, False)
                self.trigger_check2(self.events.a.trigger, True)
                self.trigger_check(self.events.b.trigger, False)
                self.trigger_check(self.events.c.trigger, False)
                with self.events.a.suppress_callback(self.on_trigger2):
                    self.trigger_check2(self.events.a.trigger, False)
                self.trigger_check2(self.events.a.trigger, True)


            self.trigger_check(self.events.a.trigger, True)
            self.trigger_check2(self.events.a.trigger, True)
            self.trigger_check(self.events.b.trigger, False)
            self.trigger_check(self.events.c.trigger, True)

        self.trigger_check(self.events.a.trigger, True)
        self.trigger_check2(self.events.a.trigger, True)
        self.trigger_check(self.events.b.trigger, True)
        self.trigger_check(self.events.c.trigger, True)



def f_a(*args): pass
def f_b(*args): pass
def f_c(*args): pass
def f_d(a, b, c): pass


class TestEventsSignatures(EventsBase):

    def setUp(self):
        self.events = he.Events()
        self.events.a = he.Event()

    def test_basic_triggers(self):
        self.events.a.connect(lambda *args, **kwargs: 0)
        self.events.a.connect(lambda: 0, None)
        self.events.a.connect(lambda x: 0, 1)
        self.events.a.connect(lambda x, y: 0, 2)
        self.events.a.connect(lambda x, y=988:
                              nt.assert_equal(y, 988), 1)
        self.events.a.connect(lambda x, y=988:
                              nt.assert_not_equal(y, 988), 2)
        self.events.a.trigger(2, 5)

        nt.assert_raises(ValueError, self.events.a.trigger)
        nt.assert_raises(ValueError, self.events.a.trigger, 2)
        self.events.a.trigger(2, 5, 8)

    def test_connected(self):
        self.events.a.connect(f_a)
        self.events.a.connect(f_a, None)
        self.events.a.connect(f_b, 2)
        self.events.a.connect(f_c, 5)
        self.events.a.connect(f_d, 'auto')

        ref = {'all': set([f_a]), 0: set([f_a]), 1: set(), 2: set([f_b]),
               3: set([f_d]), 5: set([f_c]),
               None: set([f_a, f_b, f_c, f_d])}
        for k, v in ref.iteritems():
            con = self.events.a.connected(k)
            nt.assert_equal(con, v)

        con = self.events.a.connected()
        nt.assert_equal(con, ref[None])

    @nt.raises(TypeError)
    def test_type(self):
        self.events.a.connect('f_a')


class TestTripperArgResolution(EventsBase):

    def setup(self):
        self.events = he.Events()
        self.events.a = he.Event(kwarg_order=['A', 'B'])
        self.events.b = he.Event(kwarg_order=['A', 'B', 'C'])

    def test_nargs_resolution(self):
        self.events.a.connect(lambda x=None: nt.assert_equal(x, None), 0)
        self.events.a.connect(lambda x: nt.assert_equal(x, 'vA'), 1)
        self.events.a.connect(lambda x, y:
                              nt.assert_equal((x, y), ('vA', 'vB')), 2)
        self.events.a.connect(lambda x, A:
                              nt.assert_equal((x, A), ('vA', 'vB')), 2)
        self.events.a.connect(lambda x, y=None, A=None:
                              nt.assert_equal((x, y, A),
                                              ('vA', 'vB', None)), 2)
        self.events.a.connect(lambda B, A:
                              nt.assert_equal((B, A), ('vA', 'vB')), 2)
        self.events.a.connect(lambda B, y:
                              nt.assert_equal((B, y), ('vA', 'vB')), 2)
        self.events.a.connect(lambda B, A=None:
                              nt.assert_equal(B, 'vA'), 1)
        self.events.a.connect(lambda B, y=None:
                              nt.assert_equal(B, 'vA'), 1)

        self.events.a.trigger('vA', 'vB')
        self.events.a.trigger('vA', 'vB', 'vC', 'vD')
        self.events.a.trigger(A='vA', B='vB')
        self.events.a.trigger('vA', B='vB')
        self.events.a.trigger(B='vB', A='vA')
        self.events.a.trigger('vA', C='vC', B='vB', D='vD')

    def test_all_args_resolution(self):
        self.events.a.connect(lambda x, y:
                              nt.assert_equal((x, y), ('vA', 'vB')), 'all')
        self.events.a.connect(lambda x, y, A=None, B=None:
                              nt.assert_equal((x, y, A, B),
                                              ('vA', 'vB', None, None)), 'all')

        self.events.a.trigger('vA', 'vB')

    def test_all_kwargs_resolution(self):
        self.events.a.connect(lambda A, B:
                              nt.assert_equal((A, B), ('vA', 'vB')), 'all')
        self.events.a.connect(lambda x=None, y=None, A=None, B=None:
                              nt.assert_equal((x, y, A, B),
                                              (None, None, 'vA', 'vB')), 'all')

        self.events.a.trigger(A='vA', B='vB')

    def test_all_mixed_resolution(self):
        self.events.b.connect(lambda A, B, C:
                              nt.assert_equal((A, B), ('vA', 'vB')), 'all')
        self.events.b.connect(lambda x=None, y=None, A=None, B=None, C=None:
                              nt.assert_equal((x, y, A, B, C),
                                              (None, None, 'vA', 'vB', 'vC')),
                              'all')

        self.events.a.trigger('vA', B='vC', C='vB')
        self.events.a.trigger('vA', C='vC', B='vB')

    def test_fullauto_resolution(self):
        self.events.b.connect(lambda x: nt.assert_equal(x, 'vA'), 'fullauto')
        self.events.b.connect(lambda x, A, B=None:
                              nt.assert_equal((A, B, x), ('vA', 'vB', 'vC')),
                              'fullauto')
        self.events.b.connect(lambda B, A:
                              nt.assert_equal((A, B), ('vA', 'vB')),
                              'fullauto')
        self.events.b.connect(lambda B, A=None:
                              nt.assert_equal((A, B), ('vA', 'vB')),
                              'fullauto')
        self.events.b.connect(lambda B, y=None:
                              nt.assert_equal(B, 'vB'), 'fullauto')

        self.events.b.trigger(A='vA', B='vB', C='vC', D='vD')
        self.events.b.trigger('vA', C='vC', B='vB', D='vD')
