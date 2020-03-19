# Configure the language processing service

service {'language_processing.service':
  ensure    => running,
  enable    => true,
  require   => File['language_processing.service'],
  subscribe => Exec['reload'],
}

file {'language_processing.service':
  ensure => file,
  mode   => '0644',
  owner  => 'root',
  group  => 'root',
  path   => '/etc/systemd/system/language_processing.service',
  source => '/data/current/etc/systemd/system/language_processing.service',
  notify => Exec['reload'],
}

exec {'reload':
  command => 'systemctl daemon-reload',
  path    => '/usr/bin:/bin',
}

exec {'restart':
  command => 'systemctl restart language_processing.service',
  path    => '/usr/bin:/bin',
  require => [Exec['reload'], Service['language_processing.service']],
}
