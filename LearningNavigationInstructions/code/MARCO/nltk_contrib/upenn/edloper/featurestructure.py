# Natural Language Toolkit: Feature Structures
#
# Copyright (C) 2003 University of Pennsylvania
# Author: Edward Loper <edloper@ldc.upenn.edu>,
#         Rob Speer (original code)
# URL: <http://nltk.sourceforge.net>
# For license information, see LICENSE.TXT
#
# $Id: featurestructure.py,v 1.15 2004/02/17 23:46:51 edloper Exp $


"""
Basic data classes for representing feature structures.  A X{feature
structure} is a mapping from feature names to feature values, where:

  - Each X{feature name} is a case sensitive string.
  - Each X{feature value} can be a base value (such as a string), a
    variable, or a nested feature structure.

Feature structures are typically used to represent partial information
about objects.  A feature name that is not mapped to a value stands
for a feature whose value is unknown (I{not} a feature without a
value).  Two feature structures that represent (potentially
overlapping) information about the same object can be combined by
X{unification}.  When two inconsistant feature structures are unified,
the unification fails and returns C{None}.

Features are usually specified using X{feature paths}, or tuples of
feature names that specify path through the nested feature structures
to a value.

Feature structures may contain reentrant feature values.  A
X{reentrant feature value} is a single feature value that can be
accessed via multiple feature paths.  Unification preserves the
reentrance relations imposed by both of the unified feature
structures.  After unification, any extensions to a reentrant feature
value will be visible using any of its feature paths.

Feature structure variables are encoded using the
L{FeatureStructureVariable} class.  Feature structure variables are
essentially just names; they do not directly contain values.  Instead,
the mapping from variables to values is encoded externally to the
variable, as a set of X{bindings}.  These bindings are stored using
the L{FeatureStructureVariableBinding} class, which maintains two
types of information about variables:

  - For X{bound variables}, or variables that have been assigned
    values, it records their values.
    
  - For X{unbound variables}, or variables that have not been assigned
    values, it records which variables have been set equal to each
    other, or X{merged}.  When an unbound variable is bound to a new
    value, any variables that it has been merged with will be bound to
    the same value.

@todo: more test cases
"""

# Open question: should there be a "feature" object?
#
# The current implementation doesn't actually include an object to
# encode a "feature" (i.e., a name/value pair).  This makes the code
# simpler -- one less class to deal with, and you can directly query
# for feature values, rather than going through a feature object.  But
# there might be use cases for adding a Feature object.  E.g., if we
# wanted to assign properties (like is_required) to features.  But I'd
# like to see some compelling use cases before we add it.

import re, copy
from nltk.chktype import chktype as _chktype

#//////////////////////////////////////////////////////////////////////
# Variables and variable bindings
#//////////////////////////////////////////////////////////////////////

class FeatureStructureVariable:
    """
    A variable that can stand for a single feature value in a feature
    structure.  Each variable is identified by a case sensitive
    identifier.

    Variables do not directly contain values; instead, the mapping
    from variables to values is encoded externally as a set of
    bindings, using L{FeatureStructureVariableBinding}.  If a set of
    bindings assigns a value to a variable, then that variable is said
    to be X{bound} with respect to those bindings; otherwise, it is
    said to be X{unbound}.

    @see: L{FeatureStructure}
    """
    def __init__(self, identifier):
        """
        Construct a new feature structure variable.
        @type identifier: C{string}
        @param identifier: A unique identifier for this variable.
            Any two C{FeatureStructureVariable} objects with the
            same identifier are treated as the same variable.
        """
        assert _chktype(1, identifier, str)
        self._identifier = identifier

    def identifier(self):
        """
        @return: This variable's unique identifier.
        @rtype: C{string}
        """
        return self._identifier

    def __repr__(self):
        """
        @return: A string representation of this feature structure
           variable.  A feature structure variable with identifier
           C{I{x}} is represented as C{'?I{x}'}.
        """
        return '?%s' % self._identifier

    def __cmp__(self, other):
        if not isinstance(other, FeatureStructureVariable): return -1
        return cmp(self._identifier, other._identifier)

    def __hash__(self):
        return self._identifier.__hash__()

    def merge(self, variable):
        """
        Return a merged variable that constrains this variable to be
        equal to C{variable}.
        @rtype: L{MergedFeatureStructureVariable}
        """
        if self == variable: return self
        return MergedFeatureStructureVariable(self, variable)

    def parse(s):
        # Simple variable
        match = re.match(r'\?\w+$', s)
        if match:
            return FeatureStructureVariable(match.group()[1:])

        # Merged variable
        match = re.match(r'\?<\w+(=\w+)*>$', s)
        if match:
            idents = s[2:-1].split('=')
            vars = [FeatureStructureVariable(i) for i in idents]
            return MergedFeatureStructureVariable(*vars)

        raise ValueError('Bad FeatureStructureVariable string')
    
    parse=staticmethod(parse)

class MergedFeatureStructureVariable(FeatureStructureVariable):
    """    
    A set of variables that are constrained to be equal.  A merged
    variable can be used in place of a simple variable.  In
    particular, a merged variable stands for a single feature value,
    and requires that each its subvariables are bound to that same
    value.  Merged variables can be categorized according to their
    values in a set of bindings:
    
      - A merged variable is X{unbound} if none of its subvariables
        is assigned a value.
        
      - A merged variable is X{bound} if at least one of its
        subvariables is bound, and all of its bound subvariables are
        assigned the same value.  (If at least one subvariable is
        unbound, then the merved variable is said to be X{partially
        bound}.)
        
      - A merged variable is X{inconsistant} if two or more
        subvariables are bound to different values.

    @ivar _subvariables: The set of subvariables contained by
        this merged variable.  This set is encoded as a dictionary
        whose keys are variables.
    """
    def __init__(self, *subvariables):
        """
        Construct a new feature structure variable that contains the
        given subvariables.  If C{subvariables} contains merged
        variables, then they are replaced by their lists of
        subvariables.
        @raise ValueError: If no subvariables are specified.
        """
        if len(subvariables) == 0:
            raise ValueError('Expected at least one subvariable')
        assert _chktype(1, subvariables, (FeatureStructureVariable,))
        self._subvariables = {}
        for subvar in subvariables:
            if isinstance(subvar, MergedFeatureStructureVariable):
                self._subvariables.update(subvar._subvariables)
            else:
                self._subvariables[subvar] = 1

    def identifier(self):
        """
        Raise C{ValueError}, since merged variables do not have a
        single identifier.
        """
        raise ValueError('Merged variables do not have identifiers')
    
    def subvariables(self):
        """
        @return: A list of the variables that are constrained to be
            equal by this merged variable.
        """
        return self._subvariables.keys()
    
    def __repr__(self):
        """
        @return: A string representation of this feature structure
           variable.  A feature structure variable with identifiers
           C{I{X1}, I{X2}, ..., I{Xn}} is represented as
           C{'?<I{X1}=I{X2}=...=I{Xn}>'}.
        """
        idents = [v._identifier for v in self.subvariables()]
        idents.sort()
        return '?<' + '='.join(idents) + '>'
    
    def __cmp__(self):
        if not isinstance(other, FeatureStructureVariable): return -1
        return cmp(self._subvariables, other._identifier)
    
    def __hash__(self):
        return self._subvariables.__hash__()

class FeatureStructureVariableBinding:
    """
    A partial mapping from variables to values.  Simple variables can
    be either X{bound} (i.e., assigned a value), or X{unbound} (i.e.,
    left unspecified).  Merged variables can additionally be
    X{inconsistant} (i.e., assigned multiple incompatible values).

    @ivar _bindings: A dictionary mapping from bound variables
        to their values.
    """
    def __init__(self, **initial_bindings):
        """
        Construct a new set of bindings.
        
        @param initial_bindings: A dictionary from variables to
            values, specifying the initial assignments for the bound
            variables.
        """
        # Check that variables are not used as values.
        for val in initial_bindings.values():
            if isinstance(val, FeatureStructureVariable):
                err = 'Variables cannot be bound to other variables'
                raise ValueError(err)
        
        self._bindings = initial_bindings.copy()

    def bound_variables(self):
        """
        @return: A list of all simple variables that have been
            assigned values.
        @rtype: C{list} of L{FeatureStructureVariable}
        """
        return self._bindings.keys()

    def is_bound(self, variable):
        """
        @return: True if the given variable is bound.  A simple
        variable is bound if it has been assigned a value.  A merged
        variable is bound if at least one of its subvariables is bound
        and all of its bound subvariables are assigned the same value.
        
        @rtype: C{bool}
        """
        assert _chktype(1, variable, FeatureStructureVariable)

        if isinstance(variable, MergedFeatureStructureVariable):
            bindings = [self._bindings.get(v)
                        for v in variable.subvariables()
                        if self._bindings.has_key(v)]
            if len(bindings) == 0: return 0
            inconsistant = [val for val in bindings if val != bindings[0]]
            if inconsistant: return 0
            return 1
        
        return self._bindings.has_key(variable)

    def lookup(self, variable, update_merged_bindings=False):
        """
        @return: The value that it assigned to the given variable, if
        it's bound; or the variable itself if it's unbound.  The value
        assigned to a merged variable is defined as the value that's
        assigned to its bound subvariables.

        @param update_merged_bindings: If true, then looking up a
            bound merged variable will cause any unbound subvariables
            it has to be bound to its value.  E.g., if C{?x} is bound
            to C{1} and C{?y} is unbound, then looking up C{?x=y} will
            cause C{?y} to be bound to C{1}.
        @raise ValueError: If C{variable} is a merged variable with an
            inconsistant value (i.e., if two or more of its bound
            subvariables are assigned different values).
        """
        assert _chktype(1, variable, FeatureStructureVariable)

        # If it's a merged variable, then we need to check that the
        # bindings of all of its subvariables are consistant.
        if isinstance(variable, MergedFeatureStructureVariable):
            # Get a list of all bindings.
            bindings = [self._bindings.get(v)
                        for v in variable.subvariables()
                        if self._bindings.has_key(v)]
            # If it's unbound, return the (merged) variable.
            if len(bindings) == 0: return variable
            # Make sure all the bindings are equal.
            val = bindings[0]
            for binding in bindings[1:]:
                if binding != val:
                    raise ValueError('inconsistant value')
            # Set any unbound subvariables, if requested
            if update_merged_bindings:
                for subvar in variable.subvariables():
                    self._bindings[subvar] = val
            # Return the value.
            return val

        return self._bindings.get(variable, variable)
    
    def bind(self, variable, value):
        """
        Assign a value to a variable.  If C{variable} is a merged
        variable, then the value is assigned to all of its
        subvariables.  Variables can only be bound to values; they may
        not be bound to other variables.
        
        @raise ValueError: If C{value} is a variable.
        """
        assert _chktype(1, variable, FeatureStructureVariable)
        if isinstance(value, FeatureStructureVariable):
            raise ValueError('Variables cannot be bound to other variables')
        
        if isinstance(variable, MergedFeatureStructureVariable):
            for subvar in variable.subvariables():
                self._bindings[subvar] = value
        else:
            self._bindings[variable] = value

    def copy(self):
        """
        @return: a copy of this set of bindings.
        """
        return FeatureStructureVariableBindings(**self._bindings)

    def __repr__(self):
        """
        @return: a string representation of this set of bindings.
        """
        if self._bindings:
            bindings = ['%r=%r' % (k,v) for (k,v) in self._bindings.items()]
            return '<Bindings: %s>' % (', '.join(bindings))
        else:
            return '<Bindings (empty)>'

    def __cmp__(self, other):
        if not isinstance(other, FeatureStructureVariable): return -1
        return cmp((self._bindings, self._synonyms),
                   (other._bindings, other._synonyms))

# Feature structures use identity-based-equality.
class FeatureStructure:
    """
    A structured set of features.  These features are represented as a
    mapping from feature names to feature values, where each feature
    value is either a basic value (such as a string or an integer), or
    a nested feature structure.

    A feature structure's feature values can be accessed via indexing:

      >>> fstruct1 = FeatureStructure(number='singular', person='3rd')
      >>> print fstruct1['number']
      'singular'

      >>> fstruct2 = FeatureStructure(subject=fstruct1)
      >>> print fstruct2['subject']['person']
      '3rd'

    A nested feature value can be also accessed via a X{feature
    paths}, or a tuple of feature names that specifies the paths to
    the nested feature:

      >>> fpath = ('subject','number')
      >>> print fstruct2[fpath]
      'singular'

    Feature structures may contain reentrant feature values.  A
    X{reentrant feature value} is a single feature value that can be
    accessed via multiple feature paths.

    @note: Should I present them as DAGs instead?  That would make it
        easier to explain reentrancy.
    @ivar _features: A dictionary mapping from feature names to values.

    @ivar _forward: A pointer to another feature structure that
        replaced this feature structure.  This is used during the
        unification process to preserve reentrance.  In particular, if
        we're unifying feature structures A and B, where:

          - x and y are feature paths.
          - A contains a feature structure A[x]
          - B contains a reentrant feature structure B[x]=B[y]

        Then we need to ensure that in the unified structure C,
        C[x]=C[y].  (Here the equals sign is used to denote the object
        identity relation, i.e., C{is}.)
    """
    def __init__(self, **features):
        self._features = features

    def __getitem__(self, index):
        if type(index) == str:
            return self._features[index]
        elif len(index) == 0:
            return self
        elif len(index) == 1:
            return self._features[index[0]]
        elif isinstance(self._features[index[0]], FeatureStructure):
            return self._features[index[0]][index[1:]]
        else:
            raise IndexError('Bad feature path')

    def feature_names(self):
        """
        @return: A list of the names of the features whose values are
            defined by this feature structure.
        @rtype: C{list} of C{string}
        """
        return self._features.keys()

    def equal_values(self, other, check_reentrance=False):
        """
        @return: True if C{self} and C{other} assign the same value to
        to every feature.  In particular, return true if
        C{self[M{p}]==other[M{p}]} for every feature path M{p} such
        that C{self[M{p}]} or C{other[M{p}]} is a base value (i.e.,
        not a nested feature structure).

        Note that this is a weaker equality test than L{==<__eq__>},
        which tests for equal identity.

        @param check_reentrance: If true, then any difference in the
            reentrance relations between C{self} and C{other} will
            cause C{equal_values} to return false.
        """
        if not isinstance(other, FeatureStructure): return 0
        if check_reentrances: return `self` == `other`
        if len(self._features) != len(other._features): return 0
        for (fname, selfval) in self._features.items():
            otherval = other._features[fname]
            if isinstance(selfval, FeatureStructure):
                if not selfval.equal_values(otherval): return 0
            else:
                if selfval != otherval: return 0
        return 1

    def __eq__(self, other):
        """
        @return: True if C{self} is the same object as C{other}.  This
        very strict equality test is necessary because object identity
        is used to distinguish reentrant objects from non-reentrant
        ones.
        """
        return self is other

    def __hash__(self):
        return id(self)

    def deepcopy(self, memo=None):
        """
        @return: a new copy of this feature structure.
        @param memo: The memoization dicationary, which should
            typically be left unspecified.
        """
        if memo is None: memo = {}
        memo_copy = memo.get(id(self))
        if memo_copy is not None: return memo_copy
        features = {}
        for (fname, fval) in self._features.items():
            if isinstance(fval, FeatureStructure):
                features[fname] = fval.deepcopy(memo)
            else:
                features[fname] = fval
        newcopy = FeatureStructure(**features)
        memo[id(self)] = newcopy
        return newcopy

    def apply_bindings(self, bindings):
        """
        Replace any variables bound by C{bindings} with their values.
        
        If C{self} contains a merged variable that is partially bound
        by C{bindings}, then that variable's unbound subvariables will
        be bound to its value.  E.g., if the bindings C{<?x=1>} are
        applied to the feature structure C{[A = ?<x=y>]}, then the
        bindings will be updated to C{<?x=1,?y=1>}.
        """
        selfcopy = copy.deepcopy(self)
        selfcopy._apply_bindings(bindings, {})
        return selfcopy
        
    #################################################################
    ## Unification
    #################################################################

    # The basic unification algorithm:
    #   1. Make copies of self and other (preserving reentrance)
    #   2. Destructively unify self and other
    #   3. Apply forward pointers, to preserve reentrance.
    #   4. Find any partially bound merged variables, and bind them.
    #   5. Replace bound variables with their values.
    def unify(self, other, bindings=None, trace=False):
        """
        Unify C{self} with C{other}, and return the resulting feature
        structure.  This unified feature structure is the minimal
        feature structure that:
          - contains all feature value assignments from both C{self}
            and C{other}.
          - preserves all reentrance properties of C{self} and
            C{other}.

        If no such feature structure exists (because C{self} and
        C{other} specify incompatible values for some feature), then
        unification fails, and C{unify} returns C{None}.

        @param bindings: A set of variable bindings to be used and
            updated during unification.  Bound variables are
            treated as if they were replaced by their values.  Unbound
            variables are bound if they are unified with values; or
            merged if they are unified with other unbound variables.
            If C{bindings} is unspecified, then all variables are
            assumed to be unbound.
        """
        # If bindings are unspecified, use an empty set of bindings.
        if bindings is None: bindings = FeatureStructureVariableBinding()

        # Make copies of self & other (since the unification algorithm
        # is destructive).  Use the same memo, to preserve reentrance
        # links between self and other.
        memo = {}
        selfcopy = self.deepcopy(memo)
        othercopy = other.deepcopy(memo)

        # Preserve reentrance links from bound variables into either
        # self or other.
        for var in bindings.bound_variables():
            valid = id(bindings.lookup(var))
            if memo.has_key(valid):
                bindings.bind(var, memo[valid])

        # Do the actual unification.  If it fails, return None.
        try: selfcopy._destructively_unify(othercopy, bindings, trace)
        except FeatureStructure._UnificationFailureError: return None

        # Replace any feature structure that has a forward pointer
        # with the target of its forward pointer.
        selfcopy._apply_forwards_to_bindings(bindings)
        selfcopy._apply_forwards(visited={})

        # Find any partially bound merged variables, and bind their
        # unbound subvariables.
        selfcopy._rebind_merged_variables(bindings, visited={})

        # Replace bound vars with values.
        selfcopy._apply_bindings(bindings, visited={})
        
        # Return the result.
        return selfcopy

    class _UnificationFailureError(Exception):
        """ An exception that is used by C{_destructively_unify} to
        abort unification when a failure is encountered.  """

    def _destructively_unify(self, other, bindings, trace=False, depth=0):
        """
        Attempt to unify C{self} and C{other} by modifying them
        in-place.  If the unification succeeds, then C{self} will
        contain the unified value, and the value of C{other} is
        undefined.  If the unification fails, then a
        _UnificationFailureError is raised, and the values of C{self}
        and C{other} are undefined.
        """
        if trace:
            print '|   '*depth+' /'+`self`
            print '|   '*depth+'|\\'+ `other`
        
        # Look up the "cannonical" copy of other.
        while hasattr(other, '_forward'): other = other._forward

        # Set other's forward pointer to point to self; this makes us
        # into the cannonical copy of other.
        other._forward = self

        ## This is only needed to make the trace output easier to read:
        #if trace:
        #    for (fname, selfval) in self._features.items():
        #        if not other._features.has_key(fname):
        #            print '|   '*(depth+1)
        #            print '%s|-Unify %s:' % ('|   '*(depth),fname)
        #            print 
        
        for (fname, otherval) in other._features.items():
            if trace:
                trace_otherval = otherval
                trace_selfval_defined = self._features.has_key(fname)
                trace_selfval = self._features.get(fname)
            if self._features.has_key(fname):
                selfval = self._features[fname]
                # If selfval or otherval is a bound variable, then
                # replace it by the variable's bound value.
                if isinstance(selfval, FeatureStructureVariable):
                    selfval = bindings.lookup(selfval)
                if isinstance(otherval, FeatureStructureVariable):
                    otherval = bindings.lookup(otherval)
                
                # Case 1: unify 2 feature structures (recursive case)
                if (isinstance(selfval, FeatureStructure) and
                    isinstance(otherval, FeatureStructure)):
                    selfval._destructively_unify(otherval, bindings,
                                                 trace, depth+1)

                # Case 2: unify 2 variables
                elif (isinstance(selfval, FeatureStructureVariable) and
                      isinstance(otherval, FeatureStructureVariable)):
                    self._features[fname] = selfval.merge(otherval)
                
                # Case 3: unify a variable with a value
                elif isinstance(selfval, FeatureStructureVariable):
                    bindings.bind(selfval, otherval)
                elif isinstance(otherval, FeatureStructureVariable):
                    bindings.bind(otherval, selfval)
                    
                # Case 4: unify 2 non-equal values (failure case)
                elif selfval != otherval:
                    if trace: print '|   '*depth + 'X <-- FAIL'
                    raise FeatureStructure._UnificationFailureError()

                # Case 5: unify 2 equal values
                else: pass

                if trace:
                    print '|   '*(depth+1)
                    print '%s|-Unify %s:' % ('|   '*(depth), fname)
                    print '%s|    /%r' % ('|   '*(depth), trace_selfval)
                    print '%s|   |\\%r' % ('|   '*(depth), trace_otherval)
                    print '%s|   +-->%r' % ('|   '*(depth),
                                            self._features[fname])
                    
            # Case 5: copy from other
            else:
                self._features[fname] = otherval

                
        if trace:
            print '|   '*depth+'|'
            print '|   '*depth+'+-->'+`self`
            if len(bindings.bound_variables()) > 0:
                print '|   '*depth+'    '+`bindings`
        
    def _apply_forwards_to_bindings(self, bindings):
        """
        Replace any feature structure that has a forward pointer with
        the target of its forward pointer (to preserve reentrancy).
        """
        for var in bindings.bound_variables():
            value = bindings.lookup(var)
            if (isinstance(value, FeatureStructure) and
                hasattr(value, '_forward')):
                while hasattr(value, '_forward'):
                    value = value._forward
                bindings.bind(var, value)

    def _apply_forwards(self, visited):
        """
        Replace any feature structure that has a forward pointer with
        the target of its forward pointer (to preserve reentrancy).
        """
        # Visit each node only once:
        if visited.has_key(id(self)): return
        visited[id(self)] = 1
        
        for fname, fval in self._features.items():
            if isinstance(fval, FeatureStructure):
                while hasattr(fval, '_forward'):
                    fval = fval._forward
                    self._features[fname] = fval
                fval._apply_forwards(visited)

    def _rebind_merged_variables(self, bindings, visited):
        # Visit each node only once:
        if visited.has_key(id(self)): return
        visited[id(self)] = 1
    
        for (fname, fval) in self._features.items():
            if isinstance(fval, MergedFeatureStructureVariable):
                bindings.lookup(fval, True)
            elif isinstance(fval, FeatureStructure):
                fval._rebind_merged_variables(bindings, visited)

    def _apply_bindings(self, bindings, visited):
        # Visit each node only once:
        if visited.has_key(id(self)): return
        visited[id(self)] = 1
    
        for (fname, fval) in self._features.items():
            if isinstance(fval, FeatureStructureVariable):
                if bindings.is_bound(fval):
                    self._features[fname] = bindings.lookup(fval)
            elif isinstance(fval, FeatureStructure):
                fval._apply_bindings(bindings, visited)

    #################################################################
    ## String Represenations
    #################################################################

    def __repr__(self):
        """
        Display a single-line representation of this feature structure,
        suitable for embedding in other representations.
        """
        return self._repr(self._find_reentrances({}), {})

    def __str__(self):
        """
        Display a multi-line representation of this feature structure
        as an FVM (feature value matrix).
        """
        return '\n'.join(self._str(self._find_reentrances({}), {}))

    def _repr(self, reentrances, reentrance_ids):
        """
        @return: A string representation of this feature structure.
        @param reentrances: A dictionary that maps from the C{id} of
            each feature value in self, indicating whether that value
            is reentrant or not.
        @param reentrance_ids: A dictionary mapping from the C{id}s
            of feature values to unique identifiers.  This is modified
            by C{repr}: the first time a reentrant feature value is
            displayed, an identifier is added to reentrance_ids for
            it.
        """
        segments = []

        # If this is the first time we've seen a reentrant structure,
        # then assign it a unique identifier.
        if reentrances[id(self)]:
            assert not reentrance_ids.has_key(id(self))
            reentrance_ids[id(self)] = `len(reentrance_ids)+1`

        items = self._features.items()
        items.sort() # sorting note: keys are unique strings, so we'll
                     # never fall through to comparing values.
        for (fname, fval) in items:
            if not isinstance(fval, FeatureStructure):
                segments.append('%s=%r' % (fname, fval))
            elif reentrance_ids.has_key(id(fval)):
                segments.append('%s->(%s)' % (fname,
                                              reentrance_ids[id(fval)]))
            else:
                fval_repr = fval._repr(reentrances, reentrance_ids)
                segments.append('%s=%s' % (fname, fval_repr))

        # If it's reentrant, then add on an identifier tag.
        if reentrances[id(self)]:
            return '(%s)[%s]' % (reentrance_ids[id(self)],
                                ', '.join(segments))
        else:
            return '[%s]' % (', '.join(segments))

    def _str(self, reentrances, reentrance_ids):
        """
        @return: A list of lines composing a string representation of
            this feature structure.  
        @param reentrances: A dictionary that maps from the C{id} of
            each feature value in self, indicating whether that value
            is reentrant or not.
        @param reentrance_ids: A dictionary mapping from the C{id}s
            of feature values to unique identifiers.  This is modified
            by C{repr}: the first time a reentrant feature value is
            displayed, an identifier is added to reentrance_ids for
            it.
        """
        # If this is the first time we've seen a reentrant structure,
        # then tack on an id string.
        if reentrances[id(self)]:
            assert not reentrance_ids.has_key(id(self))
            reentrance_ids[id(self)] = `len(reentrance_ids)+1`

        # Special case:
        if len(self._features) == 0:
            if reentrances[id(self)]:
                return ['(%s) []' % reentrance_ids[id(self)]]
            else:
                return ['[]']
        
        # What's the longest feature name?  Use this to align names.
        maxfnamelen = max([len(k) for k in self._features])

        lines = []
        items = self._features.items()
        items.sort() # sorting note: keys are unique strings, so we'll
                     # never fall through to comparing values.
        for (fname, fval) in items:
            if not isinstance(fval, FeatureStructure):
                # It's not a nested feature structure -- just print it.
                lines.append('%s = %r' % (fname.ljust(maxfnamelen), fval))

            elif reentrance_ids.has_key(id(fval)):
                # It's a feature structure we've seen before -- print
                # the reentrance id.
                lines.append('%s -> (%s)' % (fname.ljust(maxfnamelen),
                                               reentrance_ids[id(fval)]))

            else:
                # It's a new feature structure.  Separate it from
                # other values by a blank line.
                if lines and lines[-1] != '': lines.append('')

                # Recursively print the feature's value (fval).
                fval_lines = fval._str(reentrances, reentrance_ids)
                
                # Indent each line to make room for fname.
                fval_lines = [(' '*(maxfnamelen+3))+l for l in fval_lines]

                # Pick which line we'll display fname on.
                nameline = (len(fval_lines)-1)/2
                
                fval_lines[nameline] = (
                        fname.ljust(maxfnamelen)+' ='+
                        fval_lines[nameline][maxfnamelen+2:])

                # Add the feature structure to the output.
                lines += fval_lines
                            
                # Separate FeatureStructures by a blank line.
                lines.append('')

        # Get rid of any excess blank lines.
        if lines[-1] == '': lines = lines[:-1]
        
        # Add brackets around everything.
        maxlen = max([len(line) for line in lines])
        lines = ['[ %s%s ]' % (line, ' '*(maxlen-len(line))) for line in lines]

        # If it's reentrant, then add on an identifier tag.
        if reentrances[id(self)]:
            idstr = '(%s) ' % reentrance_ids[id(self)]
            lines = [(' '*len(idstr))+l for l in lines]
            idline = (len(lines)-1)/2
            lines[idline] = idstr + lines[idline][len(idstr):]

        return lines

    # Walk through the feature tree.  The first time we see a feature
    # value, map it to False (not reentrant).  If we see a feature
    # value more than once, then map it to C{True} (reentrant).
    def _find_reentrances(self, reentrances):
        """
        Find all of the feature values contained by self that are
        reentrant (i.e., that can be reached by multiple paths through
        feature structure's features).  Return a dictionary
        C{reentrances} that maps from the C{id} of each feature value
        to a boolean value, indicating whether it is reentrant or not.
        """
        if reentrances.has_key(id(self)):
            # We've seen it more than once.
            reentrances[id(self)] = True
        else:
            # This is the first time we've seen it.
            reentrances[id(self)] = False
        
            # Recurse to contained feature structures.
            for fval in self._features.values():
                if isinstance(fval, FeatureStructure):
                    fval._find_reentrances(reentrances)

        return reentrances

    #################################################################
    ## Parsing
    #################################################################

    def parse(s):
        """
        Convert a string representation of a feature structure (as
        displayed by repr) into a C{FeatureStructure}.  This parse
        imposes the following restrictions on the string
        representation:
          - Feature names cannot contain any of the following:
            whitespace, parenthases, quote marks, equals signs,
            dashes, and square brackets.
          - Only the following basic feature value are supported:
            strings, integers, variables, C{None}, and unquoted
            alphanumeric strings.
          - For reentrant values, the first mention must specify
            a reentrance identifier and a value; and any subsequent
            mentions must use arrows (C{'->'}) to reference the
            reentrance identifier.
        """
        try:
            value, position = FeatureStructure._parse(s, 0, {})
        except ValueError, e:
            estr = ('Error parsing field structure\n\n    ' +
                    s + '\n    ' + ' '*e.args[1] + '^ ' +
                    'Expected %s\n' % e.args[0])
            raise ValueError, estr
        if position != len(s): raise ValueError()
        return value

    # Regular expressions for parsing.
    _PARSE_RE = {'name': re.compile(r'\s*([^\s\("\'-=\[\]]+)\s*'),
                 'ident': re.compile(r'\s*\((\d+)\)\s*'),
                 'reentrance': re.compile(r'\s*->\s*'),
                 'assign': re.compile(r'\s*=\s*'),
                 'bracket': re.compile(r'\s*]\s*'),
                 'comma': re.compile(r'\s*,\s*'),
                 'none': re.compile(r'None(?=\s|\]|,)'),
                 'int': re.compile(r'-?\d+(?=\s|\]|,)'),
                 'var': re.compile(r'\?\w+'+'|'+'\?<\w+(=\w+)*>'),
                 'symbol': re.compile(r'\w+'),
                 'stringmarker': re.compile("['\"\\\\]")}

    def _parse(s, position=0, reentrances=None):
        """
        Helper function that parses a feature structure.
        @param s: The string to parse.
        @param position: The position in the string to start parsing.
        @param reentrances: A dictionary from reentrance ids to values.
        @return: A tuple (val, pos) of the feature structure created
            by parsing and the position where the parsed feature
            structure ends.
        """
        # A set of useful regular expressions (precompiled)
        _PARSE_RE = FeatureStructure._PARSE_RE

        # Check that the string starts with an open bracket.
        if s[position] != '[': raise ValueError('open bracket', position)
        position += 1

        # If it's immediately followed by a close bracket, then just
        # return an empty feature structure.
        match = _PARSE_RE['bracket'].match(s, position)
        if match is not None: return FeatureStructure(), match.end()

        # Build a list of the features defined by the structure.
        # Each feature has one of the three following forms:
        #     name = value
        #     name (id) = value
        #     name -> (target)
        features = {}
        while position < len(s):
            # Use these variables to hold info about the feature:
            name = id = target = val = None
            
            # Find the next feature's name.
            match = _PARSE_RE['name'].match(s, position)
            if match is None: raise ValueError('feature name', position)
            name = match.group(1)
            position = match.end()

            # Check for a reentrance link ("-> (target)")
            match = _PARSE_RE['reentrance'].match(s, position)
            if match is not None:
                position = match.end()
                match = _PARSE_RE['ident'].match(s, position)
                if match is None: raise ValueError('identifier', position)
                target = match.group(1)
                position = match.end()
                try: features[name] = reentrances[target]
                except: raise ValueError('bound identifier', position)

            # If it's not a reentrance link, it must be an assignment.
            else:
                match = _PARSE_RE['assign'].match(s, position)
                if match is None: raise ValueError('equals sign', position)
                position = match.end()

                # Find the feature's id (if specified)
                match = _PARSE_RE['ident'].match(s, position)
                if match is not None:
                    id = match.group(1)
                    position = match.end()
                
                val, position = FeatureStructure._parseval(s, position,
                                                           reentrances)
                features[name] = val
                if id is not None: reentrances[id] = val

            # Check for a close bracket
            match = _PARSE_RE['bracket'].match(s, position)
            if match is not None:
                return FeatureStructure(**features), match.end()

            # Otherwise, there should be a comma
            match = _PARSE_RE['comma'].match(s, position)
            if match is None: raise ValueError('comma', position)
            position = match.end()

        # We never saw a close bracket.
        raise ValueError('close bracket', position)

    def _parseval(s, position, reentrances):
        """
        Helper function that parses a feature value.  Currently
        supports: None, integers, variables, strings, nested feature
        structures.
        @param s: The string to parse.
        @param position: The position in the string to start parsing.
        @param reentrances: A dictionary from reentrance ids to values.
        @return: A tuple (val, pos) of the value created by parsing
            and the position where the parsed value ends.
        """
        # A set of useful regular expressions (precompiled)
        _PARSE_RE = FeatureStructure._PARSE_RE

        # End of string (error)
        if position == len(s): raise ValueError('value', position)
        
        # String value
        if s[position] in "'\"":
            start = position
            quotemark = s[position:position+1]
            position += 1
            while 1:
                match = _PARSE_RE['stringmarker'].search(s, position)
                if not match: raise ValueError('close quote', position)
                position = match.end()
                if match.group() == '\\': position += 1
                elif match.group() == quotemark:
                    return eval(s[start:position]), position

        # Nested feature structure
        if s[position] == '[':
            return FeatureStructure._parse(s, position, reentrances)

        # Variable
        match = _PARSE_RE['var'].match(s, position)
        if match is not None:
            return FeatureStructureVariable.parse(match.group()), match.end()

        # None
        match = _PARSE_RE['none'].match(s, position)
        if match is not None:
            return None, match.end()

        # Integer value
        match = _PARSE_RE['int'].match(s, position)
        if match is not None:
            return int(match.group()), match.end()

        # Alphanumeric symbol (must be checked after integer)
        match = _PARSE_RE['symbol'].match(s, position)
        if match is not None:
            return match.group(), match.end()

        # We don't know how to parse this value.
        raise ValueError('value', position)

    _parseval=staticmethod(_parseval)
    _parse=staticmethod(_parse)
    parse=staticmethod(parse)
    

#//////////////////////////////////////////////////////////////////////
# TESTING...
#//////////////////////////////////////////////////////////////////////

import unittest

# Note: since FeatureStructure.__repr__() sorts by keys before
# displaying, there is a single unique string repr for each
# FeatureStructure.
class FeatureStructureTestCase(unittest.TestCase):
    'Unit testing for FeatureStructure'

    def testUnification(self):
        'Basic unification tests'

        # Copying from self to other.
        fs1 = FeatureStructure(number='singular')
        fs2 = fs1.unify(FeatureStructure())
        self.failUnlessEqual(repr(fs2), "[number='singular']")

        # Copying from other to self
        fs1 = FeatureStructure()
        fs2 = fs1.unify(FeatureStructure(number='singular'))
        self.failUnlessEqual(repr(fs2), "[number='singular']")

        # Cross copying
        fs1 = FeatureStructure(number='singular')
        fs2 = fs1.unify(FeatureStructure(person=3))
        self.failUnlessEqual(repr(fs2), "[number='singular', person=3]")

        # Merging a nested structure
        fs1 = FeatureStructure(A=FeatureStructure(B='b'))
        fs2 = FeatureStructure(A=FeatureStructure(C='c'))
        fs3 = fs1.unify(fs2)
        self.failUnlessEqual(repr(fs3), "[A=[B='b', C='c']]")

    def testReentrantUnification(self):
        'Reentrant unification tests'
        # A basic case of reentrant unification
        fs1 = FeatureStructure(B='b')
        fs2 = FeatureStructure(A=fs1, E=FeatureStructure(F=fs1))
        fs3 = FeatureStructure.parse("[A=[C='c'], E=[F=[D='d']]]")
        fs4 = fs2.unify(fs3)
        fs4repr = "[A=(1)[B='b', C='c', D='d'], E=[F->(1)]]"
        self.failUnlessEqual(repr(fs4), fs4repr)
        fs5 = fs3.unify(fs2)
        fs5repr = "[A=(1)[B='b', C='c', D='d'], E=[F->(1)]]"
        self.failUnlessEqual(repr(fs5), fs5repr)

        # More than 2 paths to a value
        fs1 = FeatureStructure.parse("[a=[],b=[],c=[],d=[]]")
        fs2 = FeatureStructure()
        fs3 = FeatureStructure(a=fs2, b=fs2, c=fs2, d=fs2)
        fs4 = fs1.unify(fs3)
        self.failUnlessEqual(repr(fs4), '[a=(1)[], b->(1), c->(1), d->(1)]')
        
    def testVariableForwarding(self):
        'Bound variables should get forwarded appropriately'
        cvar = FeatureStructureVariable('cvar')
        dvar = FeatureStructureVariable('dvar')
        fs1x = FeatureStructure(X='x')
        fs1 = FeatureStructure(A=fs1x, B=fs1x, C=cvar, D=dvar)

        fs2y = FeatureStructure(Y='y')
        fs2z = FeatureStructure(Z='z')
        fs2 = FeatureStructure(A=fs2y, B=fs2z, C=fs2y, D=fs2z)

        fs3 = fs1.unify(fs2)
        fs3repr = ("[A=(1)[X='x', Y='y', Z='z'], B->(1), C->(1), D->(1)]")
        self.failUnlessEqual(repr(fs3), fs3repr)

    def testCyclicStructures(self):
        'Cyclic structure tests'
        # Create a cyclic structure via unification.
        fs1 = FeatureStructure()
        fs2 = FeatureStructure()
        fs3 = FeatureStructure(F=fs1, G=fs1)
        fs4 = FeatureStructure(F=FeatureStructure(H=fs2), G=fs2)
        fs5 = fs3.unify(fs4)

        # Check that we got the value right.
        self.failUnlessEqual(repr(fs5), '[F=(1)[H->(1)], G->(1)]')

        # Check that we got the cyclicity right.
        self.failUnless(fs5['F'] is fs5['G'])
        self.failUnless(fs5['F'] is fs5['G', 'H'])
        self.failUnless(fs5['F'] is fs5['G', 'H', 'H'])
        self.failUnless(fs5['F'] is fs5[('G',)+(('H',)*10)])

        # Create a cyclic structure with variables.
        x = FeatureStructureVariable('x')
        fs1 = FeatureStructure(F=FeatureStructure(H=x))
        fs2 = FeatureStructure(F=x)
        fs3 = fs1.unify(fs2)

        # Check that we got the value right.
        self.failUnlessEqual(repr(fs3), '[F=(1)[H->(1)]]')

        # Check that we got the cyclicity right.
        self.failUnless(fs3['F'] is fs3['F','H'])
        self.failUnless(fs3['F'] is fs3['F','H','H'])
        self.failUnless(fs3['F'] is fs3[('F',)+(('H',)*10)])

    def testVariablesPreserveReentrance(self):
        'Variable bindings should preserve reentrance.'
        bindings = FeatureStructureVariableBinding()
        fs1 = FeatureStructure.parse("[a=?x]")
        fs2 = fs1.unify(FeatureStructure.parse("[a=[]]"), bindings)
        fs3 = fs2.unify(FeatureStructure.parse("[b=?x]"), bindings)
        self.failUnlessEqual(repr(fs3), '[a=(1)[], b->(1)]')

    def testVariableMerging(self):
        'Merged variable tests'
        fs1 = FeatureStructure.parse("[a=?x, b=?x]")
        fs2 = fs1.unify(FeatureStructure.parse("[b=?y, c=?y]"))
        self.failUnlessEqual(repr(fs2), '[a=?x, b=?<x=y>, c=?y]')
        fs3 = fs2.unify(FeatureStructure.parse("[a=1]"))
        self.failUnlessEqual(repr(fs3), '[a=1, b=1, c=1]')

def testsuite():
    t1 = unittest.makeSuite(FeatureStructureTestCase)
    return unittest.TestSuite( (t1,) )

def test(verbosity):
    runner = unittest.TextTestRunner(verbosity=verbosity)
    runner.run(testsuite())

#//////////////////////////////////////////////////////////////////////
# Demo..
#//////////////////////////////////////////////////////////////////////

def display_unification(fs1, fs2, bindings, indent='  '):
    result = fs1.unify(fs2, bindings)

    # Print the two input feature structures, side by side.
    fs1_lines = str(fs1).split('\n')
    fs2_lines = str(fs2).split('\n')
    if len(fs1_lines) > len(fs2_lines):
        blankline = '['+' '*(len(fs2_lines[0])-2)+']'
        fs2_lines += [blankline]*len(fs1_lines)
    else:
        blankline = '['+' '*(len(fs1_lines[0])-2)+']'
        fs1_lines += [blankline]*len(fs2_lines)
    for (fs1_line, fs2_line) in zip(fs1_lines, fs2_lines):
        print indent + fs1_line + '   ' + fs2_line
    print indent+'-'*len(fs1_lines[0])+'   '+'-'*len(fs2_lines[0])

    linelen = len(fs1_lines[0])*2+3
    print indent+'|               |'.center(linelen)
    print indent+'+-----UNIFY-----+'.center(linelen)
    print indent+'|'.center(linelen)
    print indent+'V'.center(linelen)
    if result is None:
        print indent+'(FAILED)'.center(linelen)
    else:
        print '\n'.join([indent+l.center(linelen)
                         for l in str(result).split('\n')])
        if len(bindings.bound_variables()) > 0:
            print repr(bindings).center(linelen)
    return result

def demo(trace=False):

    HELP = '''
    1-%d: Select the corresponding feature structure
    q: Quit
    t: Turn tracing on or off
    ?: Help
    '''
    
    fstruct_strings = [
        '[agr=[number=sing, gender=masc]]',
        '[agr=[gender=masc, person=3rd]]',
        '[agr=[gender=fem, person=3rd]]',
        '[subj=[agr=(1)[]], agr->(1)]',
        '[obj=?x]',
        '[subj=?x]',
        ]
    
    fstructs = [FeatureStructure.parse(s) for s in fstruct_strings]
    bindings = FeatureStructureVariableBinding()
    
    while 1:
        print '\n'+'_'*75
        print 'Choose two feature structures to unify:'
        for i in range(len(fstructs)):
            print
            lines = str(fstructs[i]).split('\n')
            print '%3d: %s' % (i+1, lines[0])
            for line in lines[1:]: print '     '+line
        print

        selected = [None,None]
        for (nth,i) in (('First',0), ('Second',1)):
            print ('%s feature structure (1-%d,q,t,?): '
                   % (nth, len(fstructs))),
            while selected[i] is None:
                try:
                    input = sys.stdin.readline().strip()
                    if input in ('q', 'Q', 'x', 'X', ''): return
                    if input in ('t', 'T'):
                        trace = not trace; continue
                    if input in ('h', 'H', '?'):
                        print HELP % len(fstructs); continue
                    num = int(input)-1
                    selected[i] = fstructs[num]
                    print
                except:
                    print 'Bad sentence number'
                    continue

        if trace:
            result = selected[0].unify(selected[1], bindings, trace=1)
        else:
            result = display_unification(selected[0], selected[1], bindings)
        if result is not None:
            for fstruct in fstructs:
                if `result` == `fstruct`: break
            else:
                fstructs.append(result)


if __name__ == '__main__':
    #test(verbosity=2)
    demo()
