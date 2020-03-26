# Add deadsnakes PPA and install Python3.6 as default version

file {'deadsnakes':
  ensure => file,
  mode   => '0644',
  owner  => 'root',
  group  => 'root',
  path   => '/etc/apt/sources.list.d/deadsnakes-ubuntu-ppa-xenial.list',
  source => '/data/current/etc/apt/sources.list.d/deadsnakes-ubuntu-ppa-xenial.list',
}

package {'python3.6-dev':
  ensure  => installed,
  require => File['deadsnakes'],
}

package {'python3.6-venv':
  ensure  => installed,
  require => Package['python3.6-dev'],
}

file {'/usr/bin/python3':
  ensure  => link,
  source  => '/usr/bin/python3.6',
  require => Package['python3.6-dev'],
}

file {'/usr/bin/python3-config':
  ensure  => link,
  source  => '/usr/bin/python3.6-config',
  require => Package['python3.6-dev'],
}
