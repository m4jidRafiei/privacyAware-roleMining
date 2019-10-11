class PrivacyExtension():

    prefix = 'privacy:'
    uri = 'http://www.xes-standard.org/privacy.xesext'

    def __init__(self, log):
        self.log = log



    def get_current_level(self):
        try:
            level = len(self.log.attributes[self.prefix+'privacyTracking']['children'])
            return level
        except Exception as e:
            return None


    def get_methods(self,**keyparam):
        try:
            level = keyparam['level']
        except KeyError:
            level = self.get_current_level()
        try:
            return self.log.attributes[self.prefix+'privacyTracking']['children'][str(level)]['children'][self.prefix+'level']['children'][self.prefix+'methods']['children']
        except Exception as e:
            return None



    def get_statistics(self, **keyparam):
        try:
            level = keyparam['level']
        except KeyError:
            level = self.get_current_level()
        try:
            return self.log.attributes[self.prefix+'privacyTracking']['children'][str(level)]['children'][self.prefix+'level']['children'][self.prefix+'statistics']['children']
        except Exception as e:
            return None


    def get_modification_meta(self, **keyparam):
        try:
            level = keyparam['level']
        except KeyError:
            level = self.get_current_level()
        try:
            return self.log.attributes[self.prefix+'privacyTracking']['children'][str(level)]['children'][self.prefix+'level']['children'][self.prefix+'modificationMeta']['children']
        except Exception as e:
            return None

    def get_modification_data(self, **keyparam):
        try:
            level = keyparam['level']
        except KeyError:
            level = self.get_current_level()
        try:
            return self.log.attributes[self.prefix+'privacyTracking']['children'][str(level)]['children'][self.prefix+'level']['children'][self.prefix+'modificationData']['children']
        except Exception as e:
            return None


    def set_privacy_tracking(self):

        level = self.get_current_level()

        if(level is None):
            level = 1
            self.log.extensions['Privacy'] = {'prefix': self.prefix[:-1], 'uri': self.uri}
            privacyTracking = {}
        else:
            level += 1
            privacyTracking = self.log.attributes[self.prefix+'privacyTracking']

        methods = {}
        desiredAnalyses_dict = {}
        methods[self.prefix + 'method'] = ''
        methods[self.prefix + 'abstraction'] = ''
        methods[self.prefix + 'desiredAnalyses'] = {"value": None, "children": desiredAnalyses_dict}

        statistics = {}

        modificationMeta = {}
        modificationMeta[self.prefix + 'logAttributes'] = {"value": None, "children": {}}
        modificationMeta[self.prefix + 'traceAttributes'] = {"value": None, "children": {}}
        modificationMeta[self.prefix + 'eventAttributes'] = {"value": None, "children": {}}

        modificationData = {}


        # if (keyparam != {}):
        #     for key in keyparam.keys():
        #         if (key == 'methods'):
        #             methods = keyparam['methods']
        #         elif (key == 'statistics'):
        #             statistics = keyparam['statistics']
        #         elif (key == 'modificationMeta'):
        #             modificationMeta = keyparam['modificationMeta']
        #         elif (key == 'modificationData'):
        #             modificationData = keyparam['modificationData']
        #         else:
        #             keyerror = True

        if(level == 1):
            privacyTracking[str(level)] = {"value": None,
                                                       "children": {self.prefix+'level': {"value": level, "children": {
                                                           self.prefix+'methods': {"value": None, "children": methods},
                                                           self.prefix+'statistics': {"value": None, "children": statistics},
                                                           self.prefix+'modificationMeta': {"value": None,
                                                                                "children": modificationMeta},
                                                           self.prefix+'modificationData': {"value": None,
                                                                                "children": modificationData}}}}}

            self.log.attributes[self.prefix+'privacyTracking'] = {"value": None, "children": privacyTracking}
        else:
            privacyTracking['children'][str(level)] = {"value": None,
                                                       "children": {self.prefix+'level': {"value": level, "children": {
                                                           self.prefix+'methods': {"value": None, "children": methods},
                                                           self.prefix+'statistics': {"value": None, "children": statistics},
                                                           self.prefix+'modificationMeta': {"value": None,
                                                                                "children": modificationMeta},
                                                           self.prefix+'modificationData': {"value": None,
                                                                                "children": modificationData}}}}}


    def set_methods(self, method, abstraction, desiredAnalyses):

        if abstraction == True and desiredAnalyses == []:
            raise ValueError("When abstraction is 'true', the 'desiredAnalyses' list need to be set...!")

        if abstraction == False and desiredAnalyses != []:
            raise ValueError("When abstraction is 'false', the 'desiredAnalyses' list should be empty...!")

        level = self.get_current_level()
        if (level is None):
            level = 1

        methods = {}
        desiredAnalyses_dict = {}
        methods[self.prefix+'method'] = method
        methods[self.prefix+'abstraction'] = abstraction
        for index, item in enumerate(desiredAnalyses):
            desiredAnalyses_dict[str(index)] = item

        methods[self.prefix+'desiredAnalyses'] = {"value": None, "children": desiredAnalyses_dict}

        methods = {"value": None, "children": methods}

        self.log.attributes[self.prefix+'privacyTracking']['children'][str(level)]['children'][self.prefix+'level']['children'][self.prefix+'methods'] = methods

    def set_statistics(self, **keyparam):

        level = self.get_current_level()
        if (level is None):
            level = 1

        statistics = {}

        if(keyparam != {}):
            for key in keyparam.keys():
                statistics[self.prefix+key] = keyparam[key]

        statistics = {"value": None, "children": statistics}

        self.log.attributes[self.prefix+'privacyTracking']['children'][str(level)]['children'][self.prefix+'level']['children'][self.prefix+'statistics'] = statistics


    def set_modification_meta(self, logAttributes, traceAttributes, eventAttributes):

        level = self.get_current_level()
        if (level is None):
            level = 1

        modificationMeta = {}

        modificationMeta[self.prefix + 'logAttributes'] = {"value": None, "children": logAttributes}
        modificationMeta[self.prefix + 'traceAttributes'] = {"value": None, "children": traceAttributes}
        modificationMeta[self.prefix + 'eventAttributes'] = {"value": None, "children": eventAttributes}

        # if (keyparam != {}):
        #     for key in keyparam.keys():
        #             modificationMeta[self.prefix+key] = {"value": None, "children": keyparam[key]}

        modificationMeta = {"value": None, "children": modificationMeta}

        self.log.attributes[self.prefix+'privacyTracking']['children'][str(level)]['children'][self.prefix+'level']['children'][self.prefix+'modificationMeta'] = modificationMeta


    def set_modification_data(self, **keyparam):

        level = self.get_current_level()
        if (level is None):
            level = 1

        modificationData = {}

        if (keyparam != {}):
            for key_par in keyparam.keys():
                newdict = keyparam[key_par].copy()
                for key in keyparam[key_par]:
                    newdict[key] = ','.join(newdict[key])
                    newdict[self.prefix+key] = newdict.pop(key)
                    modificationData[self.prefix+key_par] = {"value": None, "children": newdict}

        # for key in organizationalPers.keys():
        #   organizationalPers[key] = ','.join(organizationalPers[key])
        # modificationData['organizationalPers'] ={"value": None, "children": organizationalPers}

        modificationData = {"value": None, "children": modificationData}

        self.log.attributes[self.prefix+'privacyTracking']['children'][str(level)]['children'][self.prefix+'level']['children'][self.prefix+'modificationData'] = modificationData
