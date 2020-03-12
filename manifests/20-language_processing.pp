# Configure the language processing service

service {'language_processing.service':
  ensure    => running,
  enable    => true,
  require   => File['language_processing.service'],
  subscribe => Exec['daemon-reload'],
}

file {'language_processing.service':
  ensure => file,
  mode   => '0644',
  owner  => 'root',
  group  => 'root',
  path   => '/etc/systemd/system/language_processing.service',
  source => '/data/current/etc/systemd/system/language_processing.service',
  notify => Exec['daemon-reload'],
}

exec {'daemon-reload':
  command     => 'systemctl daemon-reload',
  path        => '/usr/bin:/bin',
  refreshonly => true,
}
