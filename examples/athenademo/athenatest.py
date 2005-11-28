
from twisted.trial import unittest
from twisted.internet import defer

from nevow import athena, loaders, tags

class ClientToServerArgumentSerialization(athena.LiveFragment, unittest.TestCase):
    """
    Tests that arguments passed to a method on the server are properly
    received.
    """

    javascriptTest = """\
function test_ClientToServerArgumentSerialization(node) {
    var r = Nevow.Athena.refByDOM(node);
    var L = [1, 1.5, 'Hello world'];
    var O = {'hello world': 'object value'};
    return r.callRemote('test', 1, 1.5, 'Hello world', L, O);
};
"""

    docFactory = loaders.stan(tags.div(**athena.liveFragmentID)[
        tags.form(action='#', onsubmit='return test(test_ClientToServerArgumentSerialization(this));')[
            tags.input(type='submit', value='Test Client To Server Argument Serialization')]])

    allowedMethods = {'test': True}
    def test(self, i, f, s, l, d):
        self.assertEquals(i, 1)
        self.assertEquals(f, 1.5)
        self.failUnless(isinstance(s, unicode))
        self.assertEquals(s, u'Hello world')
        self.failUnless(isinstance(l[2], unicode))
        self.assertEquals(l, [1, 1.5, u'Hello world'])
        self.assertEquals(d, {u'hello world': u'object value'})
        self.failUnless(isinstance(d.keys()[0], unicode))
        self.failUnless(isinstance(d.values()[0], unicode))


class ClientToServerResultSerialization(athena.LiveFragment):
    """
    Tests that the return value from a method on the server is
    properly received by the client.
    """

    javascriptTest = """\
function test_ClientToServerResultSerialization(node) {
    var r = Nevow.Athena.refByDOM(node);
    var L = [1, 1.5, 'Hello world'];
    var O = {'hello world': 'object value'};
    var d = r.callRemote('test', 1, 1.5, 'Hello world', L, O);
    d.addCallback(function(result) {
        assertEquals(result[0], 1);
        assertEquals(result[1], 1.5);
        assertEquals(result[2], 'Hello world');
        assertEquals(result[3][0], 1);
        assertEquals(result[3][1], 1.5);
        assertEquals(result[3][2], 'Hello world');
        assertEquals(result[4]['hello world'], 'object value');
    });
    return d;
};
"""

    docFactory = loaders.stan(tags.div(**athena.liveFragmentID)[
        tags.form(action='#', onsubmit='return test(test_ClientToServerResultSerialization(this));')[
            tags.input(type='submit', value='Test Client To Server Result Serialization')]])

    allowedMethods = {'test': True}
    def test(self, i, f, s, l, d):
        return (i, f, s, l, d)

class ClientToServerExceptionResult(athena.LiveFragment):
    """
    Tests that when a method on the server raises an exception, the
    client properly receives an error.
    """

    javascriptTest = """\
function test_ClientToServerExceptionResult(node, sync) {
    var r = Nevow.Athena.refByDOM(node);
    var d;
    var s = 'This exception should appear on the client.';
    if (sync) {
        d = r.callRemote('testSync', s);
    } else {
        d = r.callRemote('testAsync', s);
    }
    d.addCallbacks(function(result) {
        fail('Erroneously received a result: ' + result);
    }, function(err) {
        var idx = (new String(err)).indexOf(s);
        if (idx == -1) {
            fail('Did not find expected message in error message: ' + err);
        }
    });
    return d;
}
"""

    docFactory = loaders.stan(tags.div(**athena.liveFragmentID)[
        tags.form(action='#', onsubmit='return test(test_ClientToServerExceptionResult(this, true));')[
            tags.input(type='submit', value='Test Client To Server Synchronous Exception Result')],
        tags.form(action='#', onsubmit='return test(test_ClientToServerExceptionResult(this, false));')[
            tags.input(type='submit', value='Test Client To Server Asynchronous Exception Result')]])


    allowedMethods = {'testSync': True, 'testAsync': True}
    def testSync(self, s):
        raise Exception(s)

    def testAsync(self, s):
        return defer.fail(Exception(s))


class AthenaTests(athena.LivePage):
    docFactory = loaders.stan([
        tags.xml('<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Strict//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd">'),
        tags.html(**{'xmlns:nevow': 'http://nevow.com/ns/nevow/0.1'})[
            tags.head[
                tags.invisible(render=tags.directive('liveglue')),
                tags.script(type='text/javascript')["""
                function test(deferred) {
                    deferred.addCallback(function (result) {
                        alert('Success!');
                    });
                    deferred.addErrback(function (err) {
                        alert('Failure: ' + err);
                    });
                    return false;
                }

                function fail(msg) {
                    throw new Error('Test Failure: ' + msg);
                }

                function assertEquals(a, b) {
                    if (!(a == b)) {
                        fail(a + ' != ' + b);
                    }
                }
                """],
                tags.slot('methods')],
            tags.body[
                tags.slot('tests')]]])

    addSlash = True

    tests = [
        ClientToServerArgumentSerialization,
        ClientToServerResultSerialization,
        ClientToServerExceptionResult,
        ]

    def renderTests(self):
        for frgClass in self.tests:
            frg = frgClass()
            frg.page = self
            yield frg

    def renderMethods(self):
        for frgClass in self.tests:
            yield tags.script(type='text/javascript')[frgClass.javascriptTest]

    def beforeRender(self, ctx):
        ctx.fillSlots('tests', self.renderTests())
        ctx.fillSlots('methods', self.renderMethods())